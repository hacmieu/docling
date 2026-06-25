# Report Entry - OCR Comparison Execution

## Run commands completed

- Tesseract baseline:
  - `--ocr-engine tesseract --ocr-lang vie,eng --ocr-psm 6`
- Tesseract full-page:
  - baseline + `--force-full-page-ocr`
- EasyOCR:
  - `--ocr-engine easyocr --ocr-lang vi,en --easyocr-confidence-threshold 0.30`

## Aggregate result snapshot

- `memory_tmp_vie_tesseract_psm6.db`: total=13, success=13, failure=0, avg markdown length=3355.92
- `memory_tmp_vie_tesseract_fullpage.db`: total=13, success=13, failure=0, avg markdown length=3320.85
- `memory_tmp_vie_easyocr.db`: total=13, success=13, failure=0, avg markdown length=3162.62
