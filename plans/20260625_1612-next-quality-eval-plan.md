# Plan Entry - Next Quality Evaluation

## Recommended next step

1. Build a small field-level benchmark set (name, id number, date) from 20-30 Vietnamese documents.
2. Score each run DB on:
   - diacritics correctness
   - key-field extraction precision/recall
   - processing time per file
3. Keep Tesseract `vie,eng + psm=6` as baseline and use full-page mode only for scan-heavy subsets.
