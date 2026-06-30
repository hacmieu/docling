# Plan — Teable ERD chuẩn hóa (DEV)

## Nguyên tắc

- **OwnCloud**: header tài liệu + OCR preview + `active_*` + link `DocExtractions`.
- **DocExtractions**: metadata AI theo version (`ai_category`, `ai_doc_type`, `ai_tags`, …).
- Không duplicate `ai_*` trên OwnCloud.

## Đã làm

1. [x] Vision 21/21 JPG + Teable incremental sync
2. [x] Sync 40 `google_vision` extractions
3. [x] Recompute effective cache 498 doc
4. [x] Script `validate_teable_erd.py`

## Còn lại (admin)

- [ ] Xóa orphan `_link_child_test` trên Teable UI/backend (foreign table missing)

## Lệnh kiểm tra

```bash
uv run python scripts/validate_teable_erd.py
```
