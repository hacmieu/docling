# Plan — DEV song song: Enrich ∥ Vision

**Thời điểm:** 2026-06-29 14:16

## Nguyên tắc DEV

Các lane **độc lập** chạy song song; chỉ post-sync chung khi cả hai xong.

```
┌─────────────────────┐     ┌──────────────────────┐
│ DeepSeek enrich     │     │ Gemini vision OCR    │
│ ai_enrich_documents │     │ run_vision_batch_sync│
│ ~4s sleep, text     │     │ ~6s sleep, 10 RPM    │
└─────────┬───────────┘     └──────────┬───────────┘
          │                            │
          └──────────┬─────────────────┘
                     ▼
        recompute_effective_metadata --sync-teable
        sync_extractions_to_teable
```

## Lane A — DeepSeek (đang chạy)

- ~454 doc HTH còn enrich
- `ai_enrich` giờ **commit từng doc** (fix mới)

## Lane B — Gemini (chờ Codex key)

1. User thêm `AI_BOX_VISION_API_KEY` (nhóm Codex) vào `.env`
2. Pilot: `run_vision_ocr_sync.py --doc-id 503`
3. Full: `run_vision_batch_sync.py` (skip doc đã có `google_vision`)

## Không song song được

- Dùng **cùng một key** cho DeepSeek text + Gemini image → provider từ chối (403).
