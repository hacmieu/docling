# OCR Pipeline Workspace

Production-oriented folder layout for OCR ingestion and evaluation workflows.

## Stage directories

- `01_inbox/`: drop new source files here (PDF, image, office docs).
- `02_manifest/`: batch manifests (`.jsonl`/`.csv`) for deterministic runs.
- `03_processing/`: files currently being processed (optional move/lock stage).
- `04_processed/`: successfully processed originals (immutable archive).
- `05_failed/`: files that failed conversion and need retry.
- `06_quarantine/`: suspicious/corrupt/password-protected files.
- `07_exports/`: generated outputs for review (markdown/json snapshots).
- `08_sqlite/`: SQLite databases (`memory_tmp.db`, `eval.db`, migrations).
- `09_logs/`: run logs, metrics, and audit traces.

## Recommended operating model

1. Place inputs in `01_inbox/`.
2. Create a run manifest in `02_manifest/` (one batch = one manifest).
3. Run ingestion script and write DB to `08_sqlite/`.
4. Move files to `04_processed/` or `05_failed/` based on status.
5. Store quality-comparison artifacts in `07_exports/` and run logs in `09_logs/`.

## Example command

```bash
uv run python scripts/folder_to_sqlite_mvp.py \
  --input-dir workspace/ocr_pipeline/01_inbox \
  --sqlite-db workspace/ocr_pipeline/08_sqlite/memory_tmp.db \
  --recursive \
  --enable-ocr
```
