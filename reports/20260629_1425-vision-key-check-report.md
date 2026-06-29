# Report — Kiểm tra lại AI_BOX_VISION và chạy Gemini

**Thời điểm:** 2026-06-29 14:25

## Kết luận ngắn

Bạn đúng: biến **`AI_BOX_VISION_API_KEY` đã có**. Lỗi trước đó do agent gán **cùng token** với `AI_BOX_API_KEY` (DeepSeek), không phải do thiếu `.env`.

Đã đặt lại key vision riêng. Kiểm tra mới:

| Kiểm tra | Kết quả |
|----------|---------|
| Key vision ≠ key text | ✅ |
| List models | ✅ `gemini-3-flash` |
| OCR ảnh PDF | ❌ **503** — không có kênh khả dụng (AI Box distributor) |

**Chưa chạy batch vision** vì mọi request sẽ fail 503 cho đến khi nhà cung cấp bật kênh Gemini cho key này.

## Cách xác nhận sẵn sàng

```bash
uv run python scripts/check_vision_api.py
# Cần: image_probe_status=200
```

## DeepSeek enrich

Vẫn chạy nền — theo dõi `09_logs/20260629_1334-ai-enrich-full.log`.
