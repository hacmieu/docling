# Report — Google Gemini Vision switch

## Cấu hình

- Vision provider: Google Generative Language API
- Model mặc định: `gemini-2.5-flash`
- API key: `GOOGLE_API_KEY` (local `.env`)

## Model khả dụng từ key hiện tại

Đã query `/v1beta/models` và thấy các model dùng được, bao gồm:
- `gemini-2.5-pro`
- `gemini-2.5-flash`
- `gemini-2.0-flash`
- `gemini-3.5-flash`
- cùng nhiều model preview/embedding/image/video khác

## Kiểm thử thực tế

- `uv run python scripts/check_vision_api.py`:
  - `models_list_status=200`
  - `image_probe_status=200`
- Pilot batch:
  - `uv run python scripts/run_vision_batch_sync.py --limit 2 --sleep-seconds 12`
  - Kết quả: `ok=2 fail=0`
  - `doc_id=504` → `extraction_id=788`, `text_len=1476`
  - `doc_id=505` → `extraction_id=790`, `text_len=1868`

## Output pilot

- Log: `workspace/ocr_pipeline/09_logs/20260629_1545-google-vision-pilot.log`
- JSON: `workspace/ocr_pipeline/09_logs/20260629_1545-google-vision-pilot.json`
