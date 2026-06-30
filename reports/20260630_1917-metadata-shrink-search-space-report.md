# Báo cáo — DeepSeek Pro lượt 2 cho text Gemini + thu hẹp tìm kiếm

**Ngày:** 2026-06-30

## Xác nhận chiến lược

**Có thể và nên làm:** dùng **Gemini Flash** chỉ để OCR ảnh, rồi đưa `raw_text` đó vào **DeepSeek v4 Pro** (lượt 2) để trích metadata — giống lane RAW (Docling markdown → DeepSeek).

Enrich **không phụ thuộc** model OCR. Input là text; output là `doc_type`, `tags`, `key_fields`, `review_vi`.

```text
Ảnh CCCD / giấy khai sinh / bằng cấp
    → Gemini Flash (model_name)     → raw_text
    → DeepSeek v4 Pro (enrich_model) → metadata lọc được
```

Pipeline đã hỗ trợ qua `PIPELINE_VISION_ENRICH_PROVIDER=aibox`.

---

## Cấu hình

```bash
PIPELINE_VISION_MODEL=gemini-2.5-flash          # OCR
PIPELINE_VISION_ENRICH_PROVIDER=aibox             # không dùng google
PIPELINE_VISION_ENRICH_MODEL=deepseek-v4-pro    # metadata
PIPELINE_RAW_ENRICH_MODEL=deepseek-v4-pro       # lane PDF/DOCX
```

**Lưu ý:** Nếu chỉ set `PIPELINE_VISION_PROVIDER=google` mà không override enrich, code **mặc định enrich cũng bằng Gemini** — cần explicit `aibox` + `deepseek-v4-pro`.

Trong Postgres/Teable:

- `model_name` = model OCR (Gemini)
- `enrich_model` = `deepseek-v4-pro`

---

## Vì sao DSv4 Pro cho lượt 2?

| Tiêu chí | Gemini enrich | DeepSeek Pro enrich |
|----------|---------------|---------------------|
| Quota | Chung bucket vision → 429 | AI Box riêng |
| JSON tiếng Việt | Tốt | Đã pilot ổn trên catalog |
| Nhất quán 2 lane | Khác model RAW vs Vision | **Cùng một enrich** |
| Chi phí | Free tier hạn chế | Theo gói AI Box |

OCR ảnh khó → Gemini. **Hiểu giấy tờ hành chính** → DeepSeek trên text đã OCR là đủ.

---

## Mục tiêu: metadata để filter, giảm không gian tìm kiếm

Hiện `/api/search` ưu tiên:

1. `phong_ban` / path OwnCloud
2. `tags`, `category` từ extraction
3. `markdown ILIKE` (tốn kém, nhiễu)

**Khi `key_fields` đầy đủ:**

```sql
-- Ví dụ: chứng chỉ còn hạn, phòng CĐHA
SELECT d.id, e.key_fields
FROM documents d
JOIN effective_document_extractions e ON e.document_id = d.id
WHERE d.owncloud_path ILIKE '%2.CĐHA%'
  AND e.doc_type LIKE 'chung-chi%'
  AND (e.key_fields->>'ngay_het_han')::date >= CURRENT_DATE;
```

→ Từ ~498 document xuống **vài chục** trước khi Q&A AI (`/api/search/qa`) chạy.

**Chuỗi lọc đề xuất:**

```text
path/phòng → doc_type → key_fields (ten, ngay_het_han) → tags/concept → markdown (cuối) → Q&A (subset nhỏ)
```

Mỗi bước giảm cardinality — metadata là bước có **tỷ lệ nén cao nhất** sau path.

---

## Việc tiếp theo (để filter thật sự hoạt động)

1. Cấu hình `.env` như trên + backfill vision bằng DeepSeek.
2. Mở rộng schema `key_fields` theo loại giấy (`metadata_schemas_vi.json`).
3. Teable views: filter `ai_doc_type` + parse `key_fields_json`.
4. (Tuỳ chọn) SQL view `document_certificate_status` cho báo cáo compliance.

---

## Tóm tắt

- **Đúng:** DeepSeek Pro lượt 2 cho cả text Gemini Flash trả về — **đã support**, chỉ cần env.
- **Mục tiêu đúng:** trích metadata để **filter trước**, thu hẹp không gian tìm kiếm; AI Q&A chỉ trên tập nhỏ.

Chi tiết: [plans/20260630_1917-gemini-ocr-deepseek-enrich-plan.md](../plans/20260630_1917-gemini-ocr-deepseek-enrich-plan.md)
