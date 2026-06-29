# Memory — Gemini Codex check

- Đã kiểm tra lại `AI_BOX_VISION_API_KEY` với `gemini-3-flash`.
- Key vision khác key text (`AI_BOX_API_KEY`) và endpoint model list trả `200`.
- Probe OCR ảnh thực tế trả `429 Resource exhausted` (thay vì `503 model_not_found` trước đây).
- Kết luận: kênh model đã có quyền; hiện bị giới hạn quota/rate ở thời điểm test.
