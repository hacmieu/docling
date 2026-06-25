# OCR SQLite SPA

Lightweight single-page web app for browsing OCR data stored in SQLite.

## Features

- List documents from `documents` table
- Filter by `status` and search by source path
- View document metadata and markdown/doc_json content
- Port availability check before server start
- Default DB comes from `../08_sqlite/ACTIVE_DB.txt`

## Run

```bash
uv run python workspace/ocr_pipeline/webapp/app.py --host 127.0.0.1 --port 8765
```

Open: `http://127.0.0.1:8765`

## Port check only

```bash
uv run python workspace/ocr_pipeline/webapp/app.py --port 8765 --check-port-only
```

## AI review (text, default API group)

Use a **default-group** API key with a text model (e.g. `deepseek-v4-pro`).  
Do not use `gemini-3-flash` for chat/text (image-only per provider policy). Codex group keys are for image models (~10 RPM).

```bash
uv run python scripts/ai_review_sqlite.py --sleep-seconds 6
```

Requires `.env` (see repo root `.env.example`).

