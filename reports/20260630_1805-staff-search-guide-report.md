# Hướng dẫn tìm kiếm nhân sự trên hệ thống Docling catalog

**Ngày:** 2026-06-30

## Kiến trúc dữ liệu (nhớ nhanh)

```text
OwnCloud path (phòng / nhân sự / loại file)
        ↓
documents (markdown OCR, status)
        ↓
document_extractions (RAW / DeepSeek / google_vision)
        ↓
effective_document_extractions (waterfall — dùng cho search)
        ↓
Teable: OwnCloud ←link→ DocExtractions
```

Metadata tìm kiếm nằm ở **DocExtractions**: `ai_category`, `ai_doc_type`, `ai_tags`, `key_fields_json`, `extracted_summary`.

---

## 1. Tìm tất cả tài liệu của một bác sĩ (Trần Đức Hiển)

### Cách A — Teable (khuyến nghị cho PCN / hành chính)

1. Mở bảng **OwnCloud** trên Teable.
2. Filter:
   - `owncloud_path` contains `TRẦN ĐỨC HIỂN` **hoặc**
   - `phong_ban` = `2.CĐHA` + tìm trong `file_name` / path.
3. Click cột **DocExtractions** → xem từng version (RAW, DeepSeek, Vision) và `key_fields_json`.

**Kết quả DEV hiện có:** 7 file (CCCD 831–832, bằng 833, chứng chỉ 834–837).

### Cách B — API catalog (port 8766)

```bash
# Khởi động webapp (nếu chưa chạy)
uv run python workspace/ocr_pipeline/webapp/pg_app.py --port 8766

# Tìm theo tên (concept + markdown + tags)
curl -s 'http://127.0.0.1:8766/api/search?q=Tr%E1%BA%A7n%20%C4%90%E1%BB%A9c%20Hi%E1%BB%83n&phong_ban=2.C%C4%90HA&limit=50' | jq .

# Hỏi đáp trên top kết quả (DeepSeek)
curl -s 'http://127.0.0.1:8766/api/search/qa?q=T%C3%B3m%20t%E1%BA%AFt%20h%E1%BB%93%20s%C6%A1%20Tr%E1%BA%A7n%20%C4%90%E1%BB%A9c%20Hi%E1%BB%83n&limit=10' | jq .
```

### Cách C — SQL Postgres (SoT)

```sql
-- Theo thư mục nhân sự (chính xác nhất)
SELECT d.id, d.owncloud_path, e.category, e.doc_type, e.key_fields
FROM documents d
LEFT JOIN effective_document_extractions e ON e.document_id = d.id
WHERE d.owncloud_path ILIKE '%TRẦN ĐỨC HIỂN%'
   OR d.owncloud_path ILIKE '%TR%E1%BA%A6N%20%C4%90%E1%BB%A8C%20HI%E1%BB%82N%'
ORDER BY d.id;

-- Theo tên trong key_fields (bắt OCR sai chính tả Hiền/Hiển)
SELECT d.id, e.key_fields->>'ten' AS ten, e.doc_type, e.extracted_summary
FROM documents d
JOIN effective_document_extractions e ON e.document_id = d.id
WHERE e.key_fields->>'ten' ILIKE '%hiển%'
   OR e.key_fields->>'ten' ILIKE '%hiền%';
```

---

## 2. Tìm bác sĩ có chứng chỉ còn hạn cho một phòng khám

### Hiện trạng

- Có `key_fields.ngay` (ngày cấp / sinh) nhưng **chưa có `ngay_het_han` thống nhất** trên mọi chứng chỉ.
- Chưa có bảng “nhân sự” riêng — nhân sự được **suy ra từ path** (`.../BÁC SĨ/<Tên>/...`) + metadata extraction.

### Cách làm được ngay (thủ công / bán tự động)

1. **Teable View DocExtractions**
   - Filter `doc_type` ∈ `chung-chi`, `chung-chi-hanh-nghe`, `chung-chi-ao-tao-lien-tuc`.
   - Filter `ai_tags` contains `chung-chi` hoặc `pham-vi-hanh-nghe`.
   - Join document → lọc `phong_ban` = phòng cần kiểm tra (vd. `2.CĐHA`).
   - Đọc `key_fields_json` + `extracted_summary` để xem ngày hết hạn (nếu OCR có).

2. **Concept search** (luật / quy định mới)

```bash
curl -s 'http://127.0.0.1:8766/api/search?q=ph%E1%BA%A1m%20vi%20h%C3%A0nh%20ngh%E1%BB%81&phong_ban=2.C%C4%90HA&limit=50'
```

Registry: `workspace/ocr_pipeline/config/concepts_vi.json` (synonym `phạm vi hành nghề`, tag `chung-chi`).

3. **SQL gợi ý** (khi đã có `ngay_het_han` sau enrich)

```sql
SELECT d.id, e.key_fields->>'ten', e.key_fields->>'ngay_het_han', e.doc_type
FROM documents d
JOIN effective_document_extractions e ON e.document_id = d.id
WHERE d.owncloud_path ILIKE '%/2.CĐHA/%'
  AND e.doc_type LIKE 'chung-chi%'
  AND (e.key_fields->>'ngay_het_han')::date >= CURRENT_DATE;
```

### Cần bổ sung để “tìm hết hạn” tự động

| Hạng mục | Hành động |
|----------|-----------|
| Enrich prompt | Thêm `ngay_het_han`, `pham_vi` vào `key_fields` |
| Concept | `chung-chi-con-han`, `het-han-chung-chi` |
| Teable | Cột formula / filter trên `key_fields_json` |
| Báo cáo định kỳ | Script SQL + export Teable View |

---

## 3. Thứ tự ưu tiên khi tìm

1. **Path / phòng ban** — thu hẹp 498 → vài chục doc.
2. **Tên trong `key_fields.ten`** — bắt biến thể OCR.
3. **Concept + tags** — chứng chỉ, hành nghề, quyết định.
4. **Q&A API** — chỉ khi cần tổng hợp câu trả lời trên subset đã lọc.

Không quét toàn bộ markdown bằng AI — luôn lọc cấu trúc trước (chi phí thấp, chính xác hơn).
