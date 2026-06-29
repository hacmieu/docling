# Report — Teable live sync

## Kết luận cho câu hỏi

Trước đó hệ thống chạy theo kiểu **Postgres (SoT) -> sync sang Teable theo job**, chưa phải ghi trực tiếp vào Teable realtime.

## Đã triển khai ngay

- Đồng bộ OwnCloud Teable:
  - `Postgres effective cache: updated=470 cleared=28`
  - `Teable PATCH: patched=475 skipped_no_record=0`
- Đồng bộ DocExtractions Teable:
  - vòng sync cuối: `total=468 created=6 updated=462 failed=0`
- Fix lỗi sync 400:
  - lọc option select theo choices Teable trước khi gửi (`ai_category`, `ai_doc_type`, `ai_tags`).

## Trạng thái chạy hiện tại

- Enrich batch chạy lại: `workspace/ocr_pipeline/09_logs/20260629_1552-ai-enrich-full.log`
- Loop sync Teable mỗi 5 phút: `workspace/ocr_pipeline/09_logs/20260629_1552-teable-sync-loop.log`
