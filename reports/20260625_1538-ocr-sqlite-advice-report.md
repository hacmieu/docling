# Report Entry - OCR and SQLite Advice

## Evidence reviewed

- Root README and examples confirming:
  - OCR support and pipeline options.
  - direct Markdown export (`export_to_markdown`).
  - structured JSON export (`export_to_dict`).

## Recommendation delivered

- Direction is correct: OCR with Docling -> store markdown + structured JSON in SQLite temporary memory.
- Suggested using SQLite as a staging layer before optional vector indexing.
