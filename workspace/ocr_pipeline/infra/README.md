# OCR Pipeline Infra

Local stack for **ownCloud Infinite Scale (OCIS)** + PostgreSQL catalog.

## OwnCloud vs Nextcloud (quan trọng)

| Sản phẩm | Image / dòng | Ghi chú |
|----------|----------------|---------|
| **ownCloud Infinite Scale (OCIS)** | `owncloud/ocis:8.0.4` | **Bản mới nhất** từ ownCloud GmbH — đang dùng |
| ownCloud Server 10.x (legacy) | `owncloud/server:10.x` | PHP cũ, vẫn là ownCloud nhưng không phải dòng mới nhất |
| **Nextcloud** | `nextcloud/*` | **Fork** tách từ ownCloud 2016 — **không dùng** |

## Start

```bash
cd workspace/ocr_pipeline/infra
docker compose up -d
```

- **OCIS UI**: https://127.0.0.1:9200 (chấp nhận cảnh báo cert self-signed; login `admin` / `admin`)
- **PostgreSQL**: `postgresql://ocr:ocr@127.0.0.1:5433/ocr_catalog`

Nếu trước đó chạy `owncloud/server` (port 8088), dừng stack cũ:

```bash
docker stop ocr-owncloud ocr-owncloud-mysql 2>/dev/null || true
```

## Workflow (PDCA)

1. **Plan**: define folder taxonomy on OCIS (e.g. `/OCR`).
2. **Do**: sync catalog → OCR ingest → AI enrich → import verified backfill.
3. **Check**: query Postgres by tag/category/FTS; spot-check AI fields.
4. **Act**: adjust tags/categories/prompt; rerun only changed docs.

## Commands

```bash
# Personal space (legacy /Yen)
uv run python scripts/owncloud_sync_catalog.py --remote-prefix /Yen

# Project Space HTH Shared Drive (khuyến nghị)
uv run python scripts/owncloud_sync_catalog.py --drive-alias project/hth-shared-drive --prune-missing

# Chỉ một phòng ban trong shared drive
uv run python scripts/owncloud_sync_catalog.py \
  --drive-alias project/hth-shared-drive \
  --remote-prefix "/Truyền Thông/7.PHỤ SẢN"
```
uv run python scripts/migrate_sqlite_to_postgres.py
uv run python scripts/ai_enrich_documents.py --sleep-seconds 6
uv run python scripts/import_verified_metadata.py \
  --input-json workspace/ocr_pipeline/02_manifest/verified_backfill.sample.json
```
