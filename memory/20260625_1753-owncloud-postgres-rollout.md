# Memory Entry - OwnCloud + PostgreSQL Rollout

- Added local infra: OwnCloud (8088) + PostgreSQL catalog (5433).
- PostgreSQL is the target SoT for paths, OCR text, AI metadata, verified backfill.
- AI enrich step now designed to set `category`, `tags`, `key_fields` during DeepSeek call.
- SQLite remains legacy staging; migrated 23 docs to Postgres.
