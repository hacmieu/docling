# Plan Entry - Vietnamese OCR Improvement

## Recommended experiments

1. Baseline:
   - `--ocr-engine tesseract --ocr-lang vie,eng --ocr-psm 6`
2. Full-page OCR for scanned/id-card-like pages:
   - add `--force-full-page-ocr`
3. EasyOCR comparison:
   - `--ocr-engine easyocr --ocr-lang vi,en --easyocr-confidence-threshold 0.30`
4. macOS native OCR comparison (Apple devices):
   - `--ocr-engine ocrmac --ocr-lang vi-VN,en-US --ocrmac-recognition accurate`

## Evaluation axis

- Character-level noise (accent marks, punctuation).
- Key-field extraction accuracy (name, ID number, date).
- Throughput/runtime for each configuration.
