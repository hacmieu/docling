# Plan Entry — PostgreSQL catalog UI

## Đã làm

- [x] `pg_app.py` + `static/catalog.html`
- [x] API: `/api/stats`, `/api/documents`, `/api/documents/{id}`

## CHECKLIST mở rộng (sau)

- [ ] Nút "OCR ngay" trên detail (gọi ingest script)
- [ ] Nút "AI enrich" một document
- [ ] Export CSV theo filter
- [ ] Auth basic nếu expose ngoài localhost
- [ ] Gộp SQLite + PG vào một app với tab chuyển backend

## Chạy

```bash
uv run python workspace/ocr_pipeline/webapp/pg_app.py --port 8766
```
