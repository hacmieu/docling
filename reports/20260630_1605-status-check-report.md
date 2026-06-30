# Báo cáo kiểm tra hiện trạng (2026-06-30 16:05)

## Kết quả kiểm tra

| Hạng mục | Trạng thái |
|---|---|
| Documents status | `498 success`, không còn `cataloged`/`failure` |
| Google Vision extractions | `19` |
| 21 JPG mới ingest | `21` doc chưa có `google_vision` |
| Git branch | `develop` đồng bộ `origin/develop` trước khi ghi log này |

## Nhận định

- Lane ingest + enrich đã hoàn tất theo mục tiêu hiện tại.
- Lane vision đang bị nghẽn quota Google free-tier; chưa xử lý xong nhóm JPG mới.

## Khuyến nghị vận hành ngay

- Chạy lại batch vision theo tuần tự chậm (`sleep 60s`), không chạy song song batch PDF và JPG.
