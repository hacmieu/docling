# Memory — Sửa AI_BOX_VISION key + chẩn đoán Gemini

**Thời điểm:** 2026-06-29 14:25

## Vấn đề user báo

- `AI_BOX_VISION_API_KEY` **đã có** trong `.env` — đúng, không phải thiếu biến.
- Lần trước agent **nhầm** khi copy trùng `AI_BOX_API_KEY` vào `AI_BOX_VISION_API_KEY` → 403.

## Đã sửa

- Khôi phục key vision riêng (token Gemini user cung cấp trước đó) vào `AI_BOX_VISION_API_KEY`.
- Xóa fallback copy key text trong `vision_tasks.py`.
- Thêm `scripts/check_vision_api.py` — list model + probe OCR ảnh thật.

## Kết quả kiểm tra (key vision đúng, khác DeepSeek)

| Bước | Kết quả |
|------|---------|
| `/v1/models` | 200 — thấy `gemini-3-flash`, `gemini-3-flash-thinking` |
| Gọi OCR ảnh doc 503 | **503** — `Không có kênh khả dụng cho model gemini-3-flash trong nhóm default (distributor)` |

→ Lỗi **phía nhà cung cấp AI Box** (chưa route kênh Gemini cho nhóm key này), không phải thiếu code hay nhầm tên Codex.

## Việc user / admin AI Box

1. Kiểm tra key `AI_BOX_VISION` thuộc nhóm có **kênh Gemini** bật.
2. Hoặc tạo key mới đúng nhóm vision, cập nhật `.env`.
3. Chạy lại: `uv run python scripts/check_vision_api.py` → phải `image_probe_status=200`.
4. Sau đó: `uv run python scripts/run_vision_batch_sync.py --sleep-seconds 6` (song song enrich).

## Enrich

- Lane DeepSeek vẫn chạy nền (~93+ OK trong log lúc kiểm tra).
