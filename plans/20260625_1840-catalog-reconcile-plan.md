# Plan Entry — Đồng bộ catalog đúng với OCIS

## Sau khi xóa file trên Cloud

Luôn chạy:

```bash
uv run python scripts/owncloud_sync_catalog.py \
  --drive-alias project/hth-shared-drive \
  --prune-missing
```

Lệnh này: sync file mới, **prune** file đã xóa, **dedupe** path trùng.

## CHECK

- [x] `COUNT` HTH-Shared trong Postgres = số file PROPFIND trên OCIS (475)
- [x] Không còn row `/Yen%` nếu đã chuyển sang Shared Drive
- [ ] UI mặc định chỉ HTH-Shared-Drive (không “Tất cả drives”)

## ACT định kỳ

- Upload/xóa trên OCIS → chạy sync `--prune-missing`
- Refresh http://127.0.0.1:8766
