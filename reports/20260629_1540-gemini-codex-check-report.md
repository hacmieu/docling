# Report — Gemini Codex test

## Kết quả test

- `models_list_status=200`
- `models_available=['gemini-3-flash', 'gemini-3-flash-thinking']`
- `image_probe_status=429` (Resource exhausted)

## Nhận định

- Trước đó lỗi `503 model_not_found`; hiện tại chuyển thành `429`, nghĩa là model đã khả dụng cho key nhưng bị giới hạn tài nguyên/quota ở thời điểm gọi.

## Lệnh đã chạy

```bash
uv run python scripts/check_vision_api.py
```
