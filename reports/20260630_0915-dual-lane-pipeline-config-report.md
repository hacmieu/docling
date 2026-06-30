# Báo cáo: Flow hai lane + cấu hình VAR

**Thời điểm:** 2026-06-30 09:15

## Tóm tắt

Pipeline được tách rõ **2 lane độc lập**, mỗi lane có bước **AI refine** riêng. Mọi model/provider/source_type đều cấu hình qua biến môi trường `PIPELINE_*`.

## Lane 1 — RAW (EasyOCR)

```
PIPELINE_RAW_OCR_ENGINE=easyocr
  → PIPELINE_SOURCE_RAW=local_llm_ocr (RAW text)
  → PIPELINE_RAW_ENRICH_MODEL=deepseek-v4-pro
  → PIPELINE_SOURCE_RAW_ENRICH=deepseek_cleanup
  → ai_category, ai_doc_type, ai_tags
```

Script: `scripts/ai_enrich_documents.py`

## Lane 2 — AI Vision

```
PIPELINE_VISION_PROVIDER=google
PIPELINE_VISION_MODEL=gemini-2.5-flash
  → PIPELINE_SOURCE_VISION=google_vision (OCR text)
  → PIPELINE_VISION_ENRICH_MODEL=deepseek-v4-pro
  → enrich trên vision raw_text → ai_* trên extraction
  → Teable sync ngay (incremental)
```

Script: `scripts/run_vision_batch_sync.py`

## Đổi provider Vision (ví dụ sau này)

```env
PIPELINE_VISION_PROVIDER=openai
PIPELINE_VISION_MODEL=gpt-4o
PIPELINE_VISION_API_URL=https://api.openai.com/v1
PIPELINE_VISION_API_KEY=sk-...
PIPELINE_SOURCE_VISION=ai_vision
```

## Re-enrich Vision đã OCR (metadata từ inherit cũ)

```bash
uv run python scripts/backfill_vision_ai_metadata.py --force
```

## Waterfall effective (không đổi logic)

`google_vision` (70) > `deepseek_cleanup` (50) > `local_llm_ocr` (30) — override bằng `PIPELINE_PRIORITY_VISION`.
