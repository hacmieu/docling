# Report Entry - Light Theme + OCR Rerun

## Webapp update

- Applied light-theme styling as default for the OCR SPA.

## OCR rerun execution

- Command used:
  - `uv run python scripts/folder_to_sqlite_mvp.py --input-dir workspace/ocr_pipeline/01_inbox --sqlite-db workspace/ocr_pipeline/08_sqlite/memory_tmp_vie_easyocr_quality.db --recursive --enable-ocr --ocr-engine easyocr --ocr-lang vi,en --easyocr-confidence-threshold 0.25 --force-full-page-ocr`
- Result:
  - `total=23`, `success=23`, `failure=0`
  - average markdown length: `2067.61`

## Port pre-check/deploy

- Port `8765` was occupied, previous process was terminated, then webapp restarted.
- Health check confirms active DB is the new quality run DB.
