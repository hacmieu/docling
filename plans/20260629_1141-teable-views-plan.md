# Plan — Teable views & concept search trên UI

## Done

- [x] Field API: 13 cột catalog
- [x] Full sync 475 row với markdown_preview + tags

## P1 — Views Teable (user UI)

- Chưa OCR (`catalog_status` = cataloged)
- Đã OCR (`catalog_status` = success)
- Đã AI (`Status` = Done)
- Group theo `phong_ban`

## P2 — Search

- Dùng Teable `search=` trên markdown_preview / ai_tags
- Hoặc concept API Postgres (sau)

## P3 — Automation

Sau OCR/AI batch → `sync_catalog_to_teable.py` cron.
