# Memory Entry — Catalog thừa & hiển thị tiếng Việt

## Vì sao vẫn nhiều bản ghi dù đã xóa file trên OCIS

1. **Sync cũ chỉ thêm**, không xóa row Postgres khi file biến mất trên OCIS.
2. **Trùng lặp lịch sử**: 477 row `/Yen` (Personal cũ) + 491 row `project/hth-shared-drive` (cùng batch).
3. **Hai biến thể đường dẫn**: URL-encoded vs Unicode NFC → 921 row nhưng chỉ 475 file thật trên OCIS.

## Đã xử lý

- `--prune-missing` + `dedupe` trong `owncloud_sync_catalog.py`
- Xóa legacy `/Yen`, `.DS_Store`, bản encoded trùng
- Kết quả: **475 HTH-Shared** (= OCIS hiện tại) + **23** bản ghi OCR inbox cũ

## UI tiếng Việt

- Font **Be Vietnam Pro**, chuẩn hóa NFC đường dẫn
- Mặc định lọc **HTH-Shared-Drive**, ẩn `.DS_Store`
