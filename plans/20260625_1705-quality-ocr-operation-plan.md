# Plan Entry - Quality OCR Operation

## Quality-first preset

- `--ocr-engine easyocr`
- `--ocr-lang vi,en`
- `--easyocr-confidence-threshold 0.25`
- `--force-full-page-ocr`

## Operational steps

1. Ingest into a fresh DB for each batch.
2. Update `ACTIVE_DB.txt` only after successful validation.
3. Keep previous DB snapshots for audit and regression comparison.
