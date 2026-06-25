# Memory — Thu hẹp không gian tìm kiếm: ví dụ «phạm vi hành nghề»

## Nhu cầu nhân viên BV

Gõ **«phạm vi hành nghề»** → hệ thống liệt kê **tất cả văn bản liên quan** trong kho OCIS/catalog, không cần biết tên file hay folder.

## Bản chất kỹ thuật

Mục tiêu không phải «AI đọc 447 PDF mỗi lần search», mà:

1. **Lúc index (một lần)**: OCR + AI gán tag/category/tóm tắt → mỗi doc có «chỉ mục ngữ nghĩa».
2. **Lúc search (miễn phí)**: gộp nhiều tín hiệu (từ khóa trong OCR, tag, category, tóm tắt) → **tập doc nhỏ có xếp hạng**.
3. **Lúc suy luận (có phí, tùy chọn)**: chỉ khi user bấm «Hỏi AI» trên **10–20 doc đã lọc**.

## Ví dụ «phạm vi hành nghề»

| Nguồn match | Ví dụ |
|-------------|-------|
| FTS `markdown` | Cụm «phạm vi hành nghề», «đăng ký hành nghề» trong OCR |
| Tag AI | `pham-vi-hanh-nghe`, `chung-chi-hanh-nghe` (kể cả khi văn bản dùng từ khác) |
| Category | *Quy định hành nghề*, *Pháp lý y tế* |
| `ai_review` | Tóm tắt AI nhắc nội dung hành nghề |
| Concept map | Query user → mở rộng đồng nghĩa trước khi search |

## Gap hiện tại

- Webapp `pg_app.py` chỉ search **đường dẫn / tên file**, chưa search **nội dung OCR**.
- Catalog ~447 PDF đã OCR; **chưa chạy AI enrich** → chưa có tag/category để match khái niệm.

## Hướng xử lý

Concept registry (`concepts_vi.json`) + multi-signal search API + enrich batch → đủ cho use case nhân viên mà không vector DB giai đoạn 1.
