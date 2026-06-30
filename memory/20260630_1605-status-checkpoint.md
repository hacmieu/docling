# Status checkpoint 2026-06-30 16:05

## Snapshot hiện trạng

- Documents trong Postgres: `498/498` ở trạng thái `success`.
- Vision extractions hiện có: `19` bản ghi `google_vision`.
- Nhóm 21 ảnh JPG mới ingest (ids: 599, 728, 747, 754-761, 776, 811, 831-837, 843) vẫn chưa có `google_vision` do quota 429.
- ASR cho doc 991 (`.m4a`) đã hoàn tất và enrich thành công ở bước trước.

## Vấn đề chính

- Các batch vision song song trước đó bị dừng (SIGTERM) và fail do Google free-tier rate limit (`429 RESOURCE_EXHAUSTED`).
- Hệ thống hiện ổn định ở lane ingest + enrich; phần còn pending là lane vision cho 21 JPG.

## Hành động tiếp theo

- Chạy lại vision theo chế độ tuần tự chậm (`--sleep-seconds 60`) và chỉ chạy một batch tại một thời điểm.
