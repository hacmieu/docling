# Memory — Teable live sync enabled

- Làm rõ kiến trúc hiện tại: pipeline ghi vào Postgres trước, sau đó sync ra Teable.
- Đã xử lý các session Postgres bị kẹt lock (ALTER TABLE chờ lock / idle transaction) để khôi phục sync.
- Chạy sync thủ công vào Teable:
  - `recompute_effective_metadata.py --sync-teable` -> patched 475 OwnCloud rows.
  - `sync_extractions_to_teable.py` -> updated 462 + created 6, failed 0 sau khi fix validate choice.
- Sửa `sync_extractions_to_teable.py` để lọc `ai_category`/`ai_doc_type`/`ai_tags` theo choices hiện có của Teable, tránh 400 invalid option.
- Bật chế độ gần realtime:
  - Restart enrich batch (`20260629_1552-ai-enrich-full.log`).
  - Bật loop sync Teable mỗi 5 phút (`20260629_1552-teable-sync-loop.log`).
