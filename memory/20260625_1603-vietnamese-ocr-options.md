# Memory Entry - Vietnamese OCR Tuning Options

- Enhanced `scripts/folder_to_sqlite_mvp.py` to support OCR engine and language tuning from CLI.
- Added OCR tuning flags:
  - `--ocr-engine` (`tesseract`, `easyocr`, `ocrmac`)
  - `--ocr-lang` (engine-specific language list)
  - `--ocr-psm` (Tesseract page segmentation mode)
  - `--easyocr-confidence-threshold`
  - `--ocrmac-recognition`
- Vietnamese-friendly defaults when OCR enabled:
  - Tesseract: `vie,eng`
  - EasyOCR: `vi,en`
  - OCRmac: `vi-VN,en-US`
