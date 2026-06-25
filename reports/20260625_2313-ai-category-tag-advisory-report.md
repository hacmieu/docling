# Report — Tư vấn AI category / tag / label vs context API email

## Câu hỏi

Liệu phương án **label, tag, category** (AI gán sau OCR) có ổn so với kinh nghiệm **API tìm email theo luồng, ngày tháng** làm context cho AI?

## Kết luận

**Có — phương án ổn và phù hợp catalog BV Hưng Thịnh**, với điều kiện coi tag/category là **lớp ngữ nghĩa bổ sung**, không thay **lớp lọc cấu trúc** giống API email.

### So sánh trực tiếp

| Email API (đã làm) | Catalog OCR (đề xuất) |
|--------------------|------------------------|
| Thread / conversation id | Folder OCIS, case folder, (sau) `related_ids` |
| Ngày gửi/nhận | `updated_at`, `ai_key_fields.ngay`, `verified_at` |
| Người gửi/nhận | `ai_key_fields.don_vi`, path phòng ban |
| Subject snippet | `ai_review`, excerpt `markdown` |
| Label Gmail | `tags` + `categories` |
| Search trong body | FTS trên `markdown` |

API email trả **tập doc nhỏ + metadata** → LLM đọc. Catalog nên **cùng pattern**: coarse filter (path, date, category, tag, FTS) → context payload → mới gọi DeepSeek.

### Category vs tag vs label

- **Category**: một nhãn chính cho navigation (10–15 giá trị chuẩn). Ví dụ: *Hợp đồng*, *Quyết định*, *Biên bản*, *Báo cáo*.
- **Tag**: nhiều facet, AI sinh tự do rồi normalize dần. Ví dụ: `dau-thau`, `bao-hiem-y-te`, `noi-bo`.
- **Label**: trong hệ thống này **gộp vào `tags`** — tránh thêm dimension thứ tư gây trùng lặp.

`ai_doc_type` + `ai_key_fields` (số, ngày, đơn vị) là **structured metadata** — tương đương header email, rất hữu ích cho filter không cần đọc full OCR.

### Chi phí (ước ~447 PDF đã OCR)

- Enrich 1 lần: ~12k chars markdown/doc, DeepSeek default group → **hàng chục nghìn token một lần**, chấp nhận được cho batch đêm.
- Search hàng ngày: **0 token** nếu chỉ filter Postgres + FTS.
- Q&A: chỉ token trên subset user chọn.

### Rủi ro và cách giảm

| Rủi ro | Giảm pháp |
|--------|-----------|
| Tag/category không nhất quán | Taxonomy file + normalize; human `verified_metadata` |
| AI hallucinate key_fields | Hiển thị "AI đề xuất" vs verified; không auto-commit pháp lý |
| OCR kém → tag sai | `ai_ocr_quality`; re-enrich sau re-OCR |
| Quá nhiều tag unique | Gom tag đồng nghĩa; giới hạn 5–8 tag/doc trong prompt |

### Khuyến nghị hành động

1. **Giữ** Postgres làm SoT; Teable chỉ mirror UI.
2. **Chạy** `ai_enrich_documents.py` pilot `--limit 20`, rồi full `--sleep-seconds 6`.
3. **Thêm** rule tag từ `owncloud_path` (phòng ban) trước AI — miễn phí, ổn định.
4. **Xây** context API giống email: query params → JSON excerpts — tái sử dụng mental model team đã quen.
5. **Không** bỏ FTS/path filter; tag/category không đủ thay date range hay dept path.

### Trạng thái code hiện tại

- Schema + script enrich: **sẵn sàng** (`scripts/ai_enrich_documents.py`).
- Full catalog **chưa enrich** (OCR xong 447 PDF, AI metadata chờ batch).
- Context API: **chưa implement** — nằm trong plan P3.

## Verdict

Phương án **label / tag / category do AI** là **đúng và tiết kiệm** cho giai đoạn hiện tại, **miễn là** luôn đi kèm **API lọc cấu trúc** (path, thời gian, luồng) như dự án email trước — đó là nền, AI metadata là lớp trên.
