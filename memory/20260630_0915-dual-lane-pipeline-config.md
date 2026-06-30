# Memory: Dual-lane pipeline + VAR config

**Thời điểm:** 2026-06-30 09:15

## Thay đổi kiến trúc

- **Lane 1:** EasyOCR → RAW → `PIPELINE_RAW_ENRICH_MODEL` → ai_* trên `PIPELINE_SOURCE_RAW_ENRICH`
- **Lane 2:** `PIPELINE_VISION_PROVIDER` OCR → `PIPELINE_VISION_ENRICH_MODEL` enrich trên vision text → ai_* trên vision row

Không còn copy metadata từ DeepSeek sang Vision (trừ khi `PIPELINE_VISION_ENRICH_FALLBACK_INHERIT=true`).

## Code mới

- `workspace/ocr_pipeline/pipeline_config.py`
- `workspace/ocr_pipeline/ai_enrich.py`

## Chọn provider sau này

Đổi `PIPELINE_VISION_PROVIDER` + key tương ứng; `PIPELINE_SOURCE_VISION` có thể đặt `ai_vision` nếu muốn tách Teable label.
