# Plan — Chuyển SoT sang Teable

## Nguyên tắc

1. **Teable** = metadata đã publish (tìm kiếm, filter, human verify).
2. **Postgres** = pipeline staging (OCR text, multi-version extractions trước publish).
3. Mọi UI tra cứu / LLM context **đọc Teable**, không đọc Postgres trực tiếp.

## Luồng mục tiêu

```text
Pipeline: OwnCloud → Postgres (OCR/enrich) → publish → Teable
Human:    Teable edit → webhook → Postgres human_verified
Search:   Teable API → llm_context_pack → LLM
```

## Việc cần làm

### Phase 1 — Đọc Teable cho search (ưu tiên)

- [ ] `teable_search.py` — list/filter OwnCloud + DocExtractions qua REST
- [ ] `pg_app.py` / `llm_context_pack` — provider `TEABLE` (env `CATALOG_SOT=teable`)
- [ ] Map field: `key_fields_json`, `ai_doc_type`, `postgres_extraction_id`

### Phase 2 — Publish rõ ràng

- [ ] Sau enrich: đánh dấu `published_to_teable_at` trên Postgres
- [ ] Chỉ row Teable `version_status=active` + link OwnCloud là “hiệu lực”

### Phase 3 — Ghi ngược Teable → Postgres

- [ ] Webhook hoặc script poll: PATCH Teable → `human_verified` extraction
- [ ] Không overwrite pipeline row đang chạy

### Phase 4 — Deprecate Postgres-only search

- [ ] `/search` mặc định Teable; Postgres chỉ `CATALOG_SOT=postgres` dev fallback

## Env

```bash
CATALOG_SOT=teable
TEABLE_API_URL=...
TEABLE_TABLE_DOCUMENTS_ID=...
TEABLE_TABLE_EXTRACTIONS_ID=...
```
