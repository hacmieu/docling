# Plan — Tìm theo khái niệm (concept search) cho nhân viên BV

## Use case mẫu

> Nhân viên gõ **«phạm vi hành nghề»** → hiện **mọi văn bản liên quan** trong hệ thống.

## Nguyên tắc

**Thu hẹp không gian trước, AI suy luận sau.**

```
447+ tài liệu
      │  search (0 token)
      ▼
  5–50 kết quả có xếp hạng + đoạn trích
      │  optional (có token)
      ▼
  AI trả lời / tổng hợp trên subset
```

## Kiến trúc 4 lớp

### L1 — Concept registry (file cấu hình, không AI)

`workspace/ocr_pipeline/config/concepts_vi.json`:

```json
{
  "pham-vi-hanh-nghe": {
    "label": "Phạm vi hành nghề",
    "synonyms": [
      "phạm vi hành nghề",
      "hành nghề y",
      "chứng chỉ hành nghề",
      "giấy phép hành nghề",
      "đăng ký hành nghề"
    ],
    "tags": ["pham-vi-hanh-nghe", "hanh-nghe", "chung-chi-hanh-nghe"],
    "categories": ["Quy định hành nghề", "Pháp lý"]
  }
}
```

- Ban đầu: **20–30 khái niệm** hay dùng ở BV (phạm vi hành nghề, đấu thầu, BHYT, hợp đồng lao động…).
- Phòng TCKT / PCN bổ sung synonym theo thực tế.

### L2 — Index phong phú (batch, một lần/doc)

1. OCR (đã xong ~447 PDF).
2. `ai_enrich_documents.py` — prompt bổ sung:
   - «Văn bản có liên quan khái niệm nào trong danh sách [concepts]?» → gán tag chuẩn.
   - `ai_review` = tóm tắt 2–3 câu (dùng cho search phụ).
3. Rule tag từ `owncloud_path` (phòng ban).

### L3 — Multi-signal search API (query time, 0 token)

`GET /api/search?q=phạm vi hành nghề&limit=50`

**Bước xử lý:**

1. Chuẩn hóa query (NFC).
2. Khớp concept registry → lấy `synonyms`, `tags`, `categories`.
3. Truy vấn Postgres **UNION có điểm**:

| Tín hiệu | Trọng số gợi ý |
|----------|----------------|
| FTS phrase trong `markdown` | 10 |
| Tag trùng `document_tags` | 8 |
| `ai_category` trùng | 6 |
| `ai_review` ILIKE synonym | 4 |
| Tên file / path ILIKE | 2 |

4. Trả về: `id`, `path`, `category`, `tags`, `score`, `snippet` (đoạn markdown quanh match).

**Postgres:** `to_tsvector('simple', markdown)` + `plainto_tsquery` cho từng synonym; hoặc `ILIKE` + `pg_trgm` nếu FTS tiếng Việt chưa đủ.

### L4 — AI suy luận (tùy chọn)

Nút **«Hỏi AI về N văn bản»** — gửi top 10–20 `snippet` + metadata → DeepSeek trả lời câu hỏi follow-up.

Không gọi LLM để **liệt kê** — chỉ để **tổng hợp / so sánh** trên tập đã thu hẹp.

## UX đề xuất (Teable hoặc webapp)

1. Ô tìm: placeholder *«VD: phạm vi hành nghề, đấu thầu, BHYT…»*
2. Bộ lọc phụ: phòng ban, năm, loại văn bản.
3. Danh sách kết quả: tên file, phòng ban, ngày, tag, **đoạn trích** in đậm cụm khớp.
4. (Sau) «Hỏi AI» trên các dòng đã chọn.

## Rollout

| Phase | Việc | Effort |
|-------|------|--------|
| **P0** | Enrich batch 447 doc + pilot 20 | 1 đêm chạy script |
| **P1** | `concepts_vi.json` 10 concept đầu (gồm phạm vi hành nghề) | vài giờ |
| **P2** | Search API multi-signal + snippet | 1–2 ngày dev |
| **P3** | Webapp/Teable: ô tìm nội dung thay vì chỉ path | 0.5 ngày |
| **P4** | Nút «Hỏi AI» trên subset | sau P2 |

## Tránh

- Embed vector toàn kho ngay — chưa cần nếu concept + FTS + tag đủ.
- Gọi LLM mỗi lần user gõ search — chậm, tốn, không deterministic.
- Chỉ exact match «phạm vi hành nghề» — bỏ sót văn bản dùng «chứng chỉ», «GP hành nghề».

## Done criteria (use case phạm vi hành nghề)

- [ ] Search trả ≥1 kết quả cho doc có cụm trong OCR **hoặ** tag `pham-vi-hanh-nghe`.
- [ ] Kết quả có snippet, sắp theo score.
- [ ] Thời gian phản hồi < 2s trên 500 doc.
- [ ] Nhân viên không cần biết đường dẫn OCIS.
