# Memory: Kiểm tra gemini-1.5-pro + so sánh 4 phiên bản

**Thời điểm:** 2026-06-29 17:48

## Probe API

- `GET /v1beta/models` → không có `gemini-1.5-pro`, `gemini-1.5-flash`.
- Có sẵn: `gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-2.5-flash-lite`, …
- `generateContent` với `gemini-1.5-pro` → **404** (model not found).
- `generateContent` với `gemini-2.5-pro` → **429** (quota exceeded) trên cùng key.

## So sánh 4 lane (3 có data + 1 blocked)

Mẫu doc 503/504/505 đã có đủ 3 extraction trong Postgres:

1. `local_llm_ocr` / EasyOCR — nhiều lỗi OCR tiếng Việt
2. `deepseek_cleanup` — summary ngắn, metadata đúng
3. `google_vision` / gemini-2.5-flash — full text tốt nhất, đang là `effective_source`
4. `gemini-1.5-pro` — không khả dụng

JSON: `workspace/ocr_pipeline/09_logs/20260629_1748-four-version-comparison.json`

## Quyết định

- Không đổi `GOOGLE_VISION_MODEL` (giữ `gemini-2.5-flash`).
- Không thêm batch 1.5-pro vào pipeline.
