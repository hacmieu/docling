# Plan Entry - OCIS Migration Checklist

## CHECK after switching to OCIS 8.0.4

- [ ] `docker compose up -d` in `workspace/ocr_pipeline/infra`
- [ ] Open https://127.0.0.1:9200 and login admin
- [ ] Create/upload folder `/OCR` on OCIS
- [ ] `owncloud_sync_catalog.py --remote-prefix /OCR` returns file paths
- [ ] Confirm Postgres catalog rows update

## ACT if legacy containers still running

- Stop old `ocr-owncloud` / `ocr-owncloud-mysql` (port 8088 stack).
