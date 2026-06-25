# Plan Entry - Production OCR Folder Strategy

## Directory lifecycle

1. Intake: put files in `workspace/ocr_pipeline/01_inbox/`.
2. Batch-control: define batch metadata in `02_manifest/`.
3. Execution: process and persist outputs to `08_sqlite/`.
4. Post-processing:
   - success -> `04_processed/`
   - failure -> `05_failed/`
   - suspicious/corrupted -> `06_quarantine/`
5. Evaluation assets:
   - generated snapshots -> `07_exports/`
   - operational logs -> `09_logs/`
