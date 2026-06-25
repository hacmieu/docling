# Report Entry - Architecture Advisory

## Question

User asked whether metadata-first indexing (path in DB + tag/category + coarse search before AI) is the right direction, and if a better low-cost alternative exists.

## Conclusion

- **Yes, this is the optimal starting path** for simple + near-free operation.
- Current MVP (OCR → SQLite → AI review column → SPA) is a valid foundation.
- Better alternative for this budget is **not** replacing SQLite with heavy vector infra now; it is **strengthening metadata + FTS + tag taxonomy** first.

## Cost control principles

- AI calls only on: enrichment batches, user-triggered analysis, final answer step on filtered docs.
- Default API group + DeepSeek text models for chat/review; separate Codex key only for image models.
- Re-OCR only when `sha256` changes.

## Next concrete build items

1. Add `nextcloud_path` (or WebDAV URI) column distinct from local ingest path.
2. Add `tags` / `categories` tables + admin UI in SPA.
3. Add SQLite FTS5 virtual table for markdown keyword search.
4. Add Nextcloud sync script (list remote files → upsert catalog → queue OCR).
