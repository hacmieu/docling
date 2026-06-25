# Report — OCIS startup & legacy ownCloud removal

## Problem

Browser error `-102` on `https://127.0.0.1:9200/` — connection refused because OCIS was not running; legacy `owncloud/server:10.15` stack still occupied the workflow on port 8088.

## Actions

1. Stopped and removed containers `ocr-owncloud`, `ocr-owncloud-mysql`.
2. Removed Docker volumes `infra_owncloud_data`, `infra_owncloud_mysql_data`.
3. Started `owncloud/ocis:8.0.4` (`ocr-owncloud-ocis`) on port **9200**.
4. Verified: `curl -sk https://127.0.0.1:9200/` → **200**; `status.php` reports Infinite Scale 10.11.

## Current stack

| Service | Container | Port |
|---------|-----------|------|
| OCIS 8.0.4 | `ocr-owncloud-ocis` | 9200 (HTTPS) |
| PostgreSQL | `ocr-pipeline-postgres` | 5433 |

Login: `admin` / `admin` (from `IDM_ADMIN_PASSWORD` in compose).

## Next

- Upload files to `/OCR` on OCIS, then run `owncloud_sync_catalog.py --remote-prefix /OCR`.
