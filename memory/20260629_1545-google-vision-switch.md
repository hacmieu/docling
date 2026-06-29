# Memory — Chuyển Vision sang Google API

- Đã thay cấu hình vision từ AI Box Vision sang Google Generative Language API bằng `GOOGLE_API_KEY`.
- Cập nhật `vision_tasks.py` để gọi endpoint Google `models/{model}:generateContent`.
- Cập nhật `check_vision_api.py` để:
  - liệt kê model từ Google API,
  - probe OCR ảnh thật.
- Test thành công:
  - `check_vision_api.py` trả `image_probe_status=200`.
  - Pilot batch `run_vision_batch_sync.py --limit 2 --sleep-seconds 12` chạy `ok=2/2`.
