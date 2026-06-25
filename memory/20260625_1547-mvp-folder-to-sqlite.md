# Memory Entry - MVP Folder to SQLite

- Added `scripts/folder_to_sqlite_mvp.py`.
- MVP behavior:
  - reads supported files from one input folder (optional recursive mode)
  - converts each file with Docling
  - stores Markdown + structured JSON + metadata in SQLite
  - records failures for later troubleshooting and comparison
