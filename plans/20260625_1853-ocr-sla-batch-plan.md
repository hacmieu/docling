# Plan Entry — OCR batch SLA

## Lệnh pilot (10 file)

```bash
uv run python scripts/owncloud_sync_catalog.py \
  --drive-alias project/hth-shared-drive --prune-missing

uv run python scripts/ocr_catalog_postgres.py --limit 10 \
  --ocr-engine easyocr --ocr-lang vi,en \
  --easyocr-confidence-threshold 0.25 --force-full-page-ocr
```

## SLA fields

| Cấp | Field |
|-----|-------|
| Batch | `batch_started_at`, `batch_finished_at`, `batch_duration_seconds` |
| File | `started_at`, `finished_at`, `duration_seconds` trong JSON report + `doc_json.ocr_sla` |

## Scale tiếp

- [ ] `--limit 50` / full queue 465 cataloged
- [ ] Song song hóa (worker pool) nếu SLA yêu cầu
- [ ] Hiển thị SLA trên webapp catalog
