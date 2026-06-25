# OCR Pipeline Infra

Local stack for OwnCloud + PostgreSQL catalog (SoT target).

## Start

```bash
cd workspace/ocr_pipeline/infra
docker compose up -d
```

- OwnCloud UI: http://127.0.0.1:8088 (default admin/admin — change after first login)
- PostgreSQL: `postgresql://ocr:ocr@127.0.0.1:5433/ocr_catalog`

Postgres uses host port **5433** to avoid conflict with other local Postgres.

## Workflow (PDCA)

1. **Plan**: define folder taxonomy on OwnCloud.
2. **Do**: sync catalog → OCR ingest → AI enrich → import verified backfill.
3. **Check**: query Postgres by tag/category/FTS; spot-check AI fields.
4. **Act**: adjust tags/categories/prompt; rerun only changed docs.

## Commands

```bash
# Sync OwnCloud paths into Postgres catalog
uv run python scripts/owncloud_sync_catalog.py --remote-prefix /OCR

# Migrate existing SQLite batch into Postgres
uv run python scripts/migrate_sqlite_to_postgres.py

# AI enrich tags/category/key_fields (DeepSeek default group)
uv run python scripts/ai_enrich_documents.py --sleep-seconds 6

# Backfill verified legacy metadata
uv run python scripts/import_verified_metadata.py \
  --input-json workspace/ocr_pipeline/02_manifest/verified_backfill.sample.json
```
