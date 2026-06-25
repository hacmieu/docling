# Plan Entry - OCR SPA Deployment

## Deployment flow

1. Validate port before run:
   - `uv run python workspace/ocr_pipeline/webapp/app.py --port 8765 --check-port-only`
2. Start server:
   - `uv run python workspace/ocr_pipeline/webapp/app.py --host 127.0.0.1 --port 8765`
3. Open UI:
   - `http://127.0.0.1:8765`

## Operational note

- Keep `ACTIVE_DB.txt` updated to switch default DB without code changes.
