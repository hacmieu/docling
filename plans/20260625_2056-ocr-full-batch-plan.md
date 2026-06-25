# Plan Entry — Full OCR batch SLA run

## Mục tiêu

OCR toàn bộ PDF `cataloged` trên HTH-Shared-Drive; đo `started_at` / `finished_at` / `duration_seconds` mỗi file + batch.

## Lệnh

```bash
uv run python scripts/ocr_catalog_postgres.py --all \
  --ocr-engine easyocr --ocr-lang vi,en \
  --easyocr-confidence-threshold 0.25 --force-full-page-ocr \
  --sla-report workspace/ocr_pipeline/09_logs/20260625_2056-ocr-full-sla.json
```

## Ước lượng

- ~437 PDF pending (sau pilot 10)
- ~10s/file → ~70–90 phút batch

## ENV Teable

Đã thêm placeholder vào `.env` (chưa sync Teable).
