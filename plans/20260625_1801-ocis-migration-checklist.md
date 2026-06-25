# Plan Entry - OCIS Migration Checklist

## CHECK after switching to OCIS 8.0.4

- [x] `docker compose up -d ocis` in `workspace/ocr_pipeline/infra` (2026-06-25)
- [x] https://127.0.0.1:9200 returns HTTP 200 (`status.php` → Infinite Scale 10.11)
- [ ] Open UI, accept self-signed cert, login `admin` / `admin`
- [ ] Create/upload folder `/OCR` on OCIS
- [ ] `owncloud_sync_catalog.py --remote-prefix /OCR` returns file paths
- [ ] Confirm Postgres catalog rows update

## ACT — legacy stack removed (2026-06-25)

- [x] Stopped/removed `ocr-owncloud` + `ocr-owncloud-mysql` (port 8088)
- [x] Removed volumes `infra_owncloud_data`, `infra_owncloud_mysql_data`
