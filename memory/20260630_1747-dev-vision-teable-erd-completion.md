# DEV completion — Vision 21 JPG + Teable ERD

**Thời điểm:** 2026-06-30 17:47

## Vision lane (21 JPG)

| Metric | Kết quả |
|--------|---------|
| Batch chính | 19 OK, 2 fail (760: 503, 831: timeout) |
| Retry 760 | OK |
| Retry 831 (timeout 300s + resize) | OK |
| **Tổng 21/21** | `google_vision` extraction đủ |

Doc 831: `CCCD MẶT SAU.jpg` — cần timeout dài + resize edge max 2048px.

## Teable ERD

- **DocExtractions**: 17 fields, đủ canonical (gồm `prompt_name`).
- **OwnCloud**: 16 fields chuẩn + link `DocExtractions` đúng `tblnLAXYbsxFtuFhbJa`.
- Còn **1 orphan**: `_link_child_test` (foreign table `tblD1vnYkb3OSzAQHlh` đã mất) — API không xóa được, cần admin Teable.

## Đồng bộ sau vision

- `sync_extractions_to_teable.py --source-type google_vision`: 40 rows updated.
- `recompute_effective_metadata.py`: 498 documents cache effective.

## Code

- `vision_tasks.py`: resize ảnh lớn, timeout 300s, retry 503/timeout.
- `teable_catalog.py`: `CANONICAL_OWN_CLOUD_FIELD_NAMES`.
- `scripts/validate_teable_erd.py`: audit ERD.
