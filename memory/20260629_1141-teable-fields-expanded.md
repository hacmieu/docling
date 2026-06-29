# Memory — Teable schema mở rộng qua Field API

## Đã làm

- API `POST /table/{id}/field` tạo **13 cột mới** trên bảng OwnCloud.
- Module `workspace/ocr_pipeline/teable_catalog.py` + `setup_teable_catalog_fields.py`.
- `sync_catalog_to_teable.py` sync đầy đủ: path, phòng ban, markdown_preview, AI metadata, OCR SLA.
- Resync **475/475** PATCH thành công (~227s).

## Cột Teable (16 field)

MVP: Label, Number, Status + owncloud_path, file_name, phong_ban, catalog_status, markdown_preview, ocr_duration_s, ocr_started_at, ocr_finished_at, ai_category, ai_doc_type, ai_tags, ai_review, updated_at.

## Lệnh

```bash
uv run python scripts/setup_teable_catalog_fields.py
uv run python scripts/sync_catalog_to_teable.py --ensure-fields
```
