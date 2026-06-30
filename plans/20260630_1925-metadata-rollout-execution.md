# Execution — Rollout metadata schema + DeepSeek enrich

## Done

- [x] Env aibox + deepseek-v4-pro for vision enrich
- [x] Two-step enrich in `ai_enrich.py`
- [x] `metadata_schemas_vi.json` (10 doc types + default)
- [x] SQL view `document_certificate_status`
- [x] Vision backfill batch (40 extractions)

## Pending

- [ ] Teable sync after backfill completes
- [ ] Full RAW lane re-enrich (`ai_enrich_documents --force`) — ~498 doc, ~1–2 API calls each
- [ ] Teable select options for new doc_types if missing

## Commands

```bash
uv run python scripts/backfill_vision_ai_metadata.py --force --sleep-seconds 4
uv run python scripts/sync_extractions_to_teable.py
uv run python scripts/ai_enrich_documents.py --force --sleep-seconds 4  # RAW lane full
```
