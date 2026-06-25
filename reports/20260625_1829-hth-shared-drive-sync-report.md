# Report — Sync HTH-Shared-Drive vào Postgres

## Thực hiện

1. Cập nhật `owncloud_sync_catalog.py`: `--drive-alias` cho Project Space OCIS.
2. Chạy sync:

```bash
uv run python scripts/owncloud_sync_catalog.py --drive-alias project/hth-shared-drive
```

## Kết quả

| Chỉ số | Giá trị |
|--------|---------|
| Drive | `project/hth-shared-drive` (HTH-Shared-Drive) |
| File sync | **491** |
| Trạng thái | `cataloged` |
| Chưa OCR | 491 |

## Cấu trúc OCIS

```
HTH-Shared-Drive/
└── Truyền Thông/
    ├── 2.CĐHA/
    ├── 7.PHỤ SẢN/
    ├── 14.ĐIỀU DƯỠNG/
    └── ...
```

## Bước kế tiếp

OCR batch từ OCIS WebDAV (download + Docling) — chưa có script; đây là blocker cho AI enrich hàng loạt.
