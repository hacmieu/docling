# Memory Entry - OCR and SQLite Direction

- User goal: OCR documents, convert to Markdown, store in temporary SQLite memory.
- Assessment: this is a valid and practical direction.
- Recommended persisted artifacts per document:
  - markdown text (`export_to_markdown`)
  - structured JSON (`export_to_dict`)
  - metadata (source path, hash, created_at, pipeline settings)
