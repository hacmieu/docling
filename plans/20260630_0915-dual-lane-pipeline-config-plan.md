# Plan: Hai lane pipeline có enrich riêng (config VAR)

**Thời điểm:** 2026-06-30 09:15

## Flow mục tiêu

```text
Lane 1 (RAW):
  EasyOCR [PIPELINE_RAW_OCR_*]
    → local_llm_ocr [PIPELINE_SOURCE_RAW]
    → DeepSeek enrich [PIPELINE_RAW_ENRICH_MODEL]
    → deepseek_cleanup [PIPELINE_SOURCE_RAW_ENRICH]
    → ai_category / ai_doc_type / ai_tags

Lane 2 (Vision):
  AI Vision [PIPELINE_VISION_PROVIDER + PIPELINE_VISION_MODEL]
    → google_vision (hoặc PIPELINE_SOURCE_VISION)
    → AI enrich trên vision text [PIPELINE_VISION_ENRICH_MODEL]
    → ai_* trên cùng extraction row
    → Teable sync ngay
```

## Module

| File | Vai trò |
|------|---------|
| `pipeline_config.py` | Đọc toàn bộ VAR từ `.env` |
| `ai_enrich.py` | `call_ai_enrich`, `enrich_extraction_from_ocr_text` |
| `vision_tasks.py` | OCR → enrich lane 2 |
| `ai_enrich_documents.py` | Batch lane 1 (dùng chung `ai_enrich`) |

## VAR chính (`.env.example`)

- `PIPELINE_RAW_OCR_ENGINE`, `PIPELINE_RAW_OCR_MODEL`
- `PIPELINE_RAW_ENRICH_MODEL`, `PIPELINE_SOURCE_RAW_ENRICH`
- `PIPELINE_VISION_PROVIDER`, `PIPELINE_VISION_MODEL`, `PIPELINE_SOURCE_VISION`
- `PIPELINE_VISION_ENRICH_MODEL`, `PIPELINE_VISION_ENRICH_ENABLED`
- `PIPELINE_ENRICH_API_URL`, `PIPELINE_ENRICH_API_KEY`

## Migration

- Bỏ inherit mặc định; `--force` backfill re-enrich vision text:
  `uv run python scripts/backfill_vision_ai_metadata.py --force`
