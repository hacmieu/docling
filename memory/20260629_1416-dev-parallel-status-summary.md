# Memory — Tổng kết dự án OCR HTH + chạy song song DEV

**Thời điểm:** 2026-06-29 14:16

## Đã làm được (tích lũy)

### Hạ tầng
- **OCIS** `HTH-Shared-Drive` → **Postgres** `ocr_catalog` (475 doc catalog)
- **OCR local** EasyOCR: ~447 PDF `success`, markdown trong `documents`
- **Teable** noibo: OwnCloud + DocExtractions + PromptTemplates; sync 475 row

### Metadata đa phiên bản (waterfall)
- `document_extractions` + view `effective_document_extractions`
- Priority: human_verified (100) → … → local_llm_ocr (30)
- Cache `effective_*` trên `documents`; Teable `active_priority` / `active_source`
- Dọn field thừa OwnCloud (`ai_category`, `ai_tags`, …)

### Tìm kiếm nhân viên
- `concept_search.py` + `concepts_vi.json`
- `GET /api/search`, `GET /api/search/qa` (DeepSeek trên top-10 excerpt)

### AI đang chạy song song (DEV)
| Lane | Script | Trạng thái |
|------|--------|------------|
| DeepSeek enrich | `ai_enrich_documents.py` | 🔄 nền, ~80+ OK trong log |
| Gemini vision | `run_vision_batch_sync.py` | ⚠️ **403** — cần API key nhóm **Codex** |

### Gemini vision — vì sao chưa chạy được
- Pilot doc 503 → `403 Forbidden` với key nhóm mặc định (DeepSeek).
- `gemini-3-flash` **chỉ** dùng key Codex (~10 RPM), không dùng chung `AI_BOX_API_KEY`.
- Code + batch script đã sẵn; chỉ cần `AI_BOX_VISION_API_KEY=<codex-key>` trong `.env`.

## Lệnh song song (sau khi có Codex key)

```bash
# Lane 1 — DeepSeek enrich (đang chạy)
tail -f workspace/ocr_pipeline/09_logs/20260629_1334-ai-enrich-full.log

# Lane 2 — Gemini vision (song song)
uv run python scripts/run_vision_batch_sync.py --sleep-seconds 6 \
  --log-file workspace/ocr_pipeline/09_logs/20260629_vision-batch.log
```

## Sau cả hai lane xong

```bash
uv run python scripts/recompute_effective_metadata.py --sync-teable
uv run python scripts/sync_extractions_to_teable.py
```
