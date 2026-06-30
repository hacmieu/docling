# UI tìm kiếm metadata + DeepSeek

**Ngày:** 2026-06-30 22:40

## URL

`http://127.0.0.1:8766/search`

## API

- `GET /api/search/context?mode=staff|degrees&q=...`
- `POST /api/search/synthesize` — `{question, llm_prompt_block, doc_count}`

## Files

- `webapp/static/search.html`
- `pg_app.py` — routes + POST handler
- `search_qa.synthesize_from_context_pack`
