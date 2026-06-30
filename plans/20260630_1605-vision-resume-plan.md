# Plan 2026-06-30 16:05 — Resume Vision JPG

## Mục tiêu

Hoàn tất lane vision cho 21 ảnh JPG chưa có `google_vision` extraction, đồng bộ Teable sau mỗi document.

## Trình tự thực thi

1. Xác nhận không có batch vision nào đang chạy nền.
2. Chạy một batch duy nhất cho danh sách 21 doc-id.
3. Cấu hình `--sleep-seconds 60` để tránh vượt free-tier quota.
4. Bật `--sync-teable` để cập nhật Teable ngay sau mỗi extraction thành công.
5. Theo dõi log và dừng sớm nếu quota tiếp tục bị 429 kéo dài.

## Tiêu chí hoàn tất

- `vision_missing_21 = 0`.
- Log batch có `ok=21`, `fail=0` (hoặc ghi rõ các doc còn fail để retry vòng sau).
