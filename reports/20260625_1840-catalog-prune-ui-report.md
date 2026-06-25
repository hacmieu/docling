# Report — Dọn catalog & sửa UI tiếng Việt

## Vấn đề

User xóa file trên OCIS nhưng UI Postgres vẫn ~991 bản ghi; tên file tiếng Việt hiển thị lỗi.

## Nguyên nhân

| Nguyên nhân | Số lượng ước lượng |
|-------------|-------------------|
| Legacy Personal `/Yen` | 477 |
| Trùng encoded vs NFC | ~446 |
| `.DS_Store` | 16 |
| OCR inbox cũ (local path) | 23 (giữ lại) |

## Sửa code

- `owncloud_sync_catalog.py`: `--prune-missing`, skip dotfiles, `dedupe_catalog_paths`, `normalize_path` NFC
- `pg_app.py` + `catalog.html`: Be Vietnam Pro, lọc mặc định HTH, ẩn `.DS_Store`

## Kết quả sau reconcile

| Metric | Giá trị |
|--------|---------|
| OCIS HTH-Shared | 475 file |
| Postgres HTH-Shared | **475** |
| Tổng Postgres | 498 (gồm 23 OCR inbox pilot) |

## Lệnh duy trì

```bash
uv run python scripts/owncloud_sync_catalog.py \
  --drive-alias project/hth-shared-drive --prune-missing
```

Webapp: http://127.0.0.1:8766 (hard refresh Ctrl+Shift+R)
