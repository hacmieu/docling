# Memory Entry - Architecture Direction Discussion

## User goal

- Nextcloud/OwnCloud là nơi lưu file gốc (đường dẫn là source of truth).
- SQLite làm catalog/index: metadata, tag, category, OCR text, AI review.
- Luồng: tìm kiếm thô (metadata/tag/keyword) trước → chỉ đưa tập nhỏ vào AI sau.

## Assessment

- Hướng này **đúng và phù hợp** mục tiêu đơn giản, chi phí thấp.
- Khớp mô hình "catalog + enrichment", tránh đốt token AI cho toàn bộ kho ngay từ đầu.
