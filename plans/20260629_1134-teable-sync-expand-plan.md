# Plan — Mở rộng Teable sau sync MVP

## Đã xong (MVP)

- `sync_catalog_to_teable.py` + `.env` noibo token/table id.
- 475 doc `project/hth-shared-drive` → Teable OwnCloud.

## Mapping hiện tại

| Teable | Postgres |
|--------|----------|
| Label | `tên file — ai_category` |
| Number | `documents.id` |
| Status | cataloged→To do; OCR success→In progress; OCR+AI→Done |

## P1 — Thêm cột trên Teable (user)

Gợi ý: `owncloud_path`, `phong_ban`, `markdown_preview`, `ai_tags`, `ai_review`, `ocr_duration_s`, `updated_at`.

## P2 — Script

- Env `TEABLE_FIELD_*` cho từng cột mới.
- Re-sync `--limit 0` (upsert theo Number).

## P3 — Views Teable

- Đã OCR / Chưa OCR / Theo phòng ban.
