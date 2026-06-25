# Plan Entry - Next Evaluation Step After Ingestion

## Immediate follow-up

1. Sample-check markdown quality from SQLite records.
2. Run a second pass with alternate OCR settings for comparison:
   - baseline: `--enable-ocr`
   - compare: `--enable-ocr --force-full-page-ocr`
3. Store comparison outputs in `workspace/ocr_pipeline/07_exports/`.
