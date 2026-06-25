# Report — PostgreSQL catalog webapp triển khai

## Deliverable

Giao diện quản lý catalog OCR đọc **PostgreSQL**: danh sách dạng **bảng**, click mở **detail**.

## Files

| File | Mô tả |
|------|-------|
| `webapp/pg_app.py` | HTTP server + API Postgres |
| `webapp/static/catalog.html` | Table list + detail panel |
| `webapp/README.md` | Hướng dẫn chạy |

## Chạy thử

```bash
uv run python workspace/ocr_pipeline/webapp/pg_app.py --host 127.0.0.1 --port 8766
```

URL: http://127.0.0.1:8766

## Smoke test (2026-06-25)

- `/api/stats`: total=991, hth_shared=491, cataloged=968
- `/api/documents?drive=project/hth-shared-drive`: OK
- Detail endpoint: OK

## Tính năng UI

- Cột: ID, File, OCIS path, Status, OCR length, AI status, Category, Updated
- Filter: status, drive, search
- Pagination 50/trang
- Detail: markdown, AI review, tags, key fields, verified metadata
