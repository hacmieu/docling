# Memory — DEV sequential: Vision, Search Q&A, AI enrich

**Thời điểm:** 2026-06-29 13:34

## Thứ tự đã chạy

### 1. Pilot Vision OCR
- `run_vision_ocr_sync.py --doc-id 503 --dry-run` → file PDF local OK.
- Gọi Gemini thất bại: **`.env` chưa có `AI_BOX_VISION_API_KEY`** (nhóm Codex, image-only).
- Cần user thêm key rồi chạy lại:
  ```bash
  uv run python scripts/run_vision_ocr_sync.py --doc-id 503
  ```

### 2. DeepSeek Search Q&A
- Module `search_qa.py` + `GET /api/search/qa?q=...`
- Pilot «phạm vi hành nghề» → 10 hit, DeepSeek trả lời (~9s), refs doc_id 506,510,…

### 3. AI enrich
- Pilot 5 doc: **5/5 OK** (~28s/doc), SLA `09_logs/20260629_1329-ai-enrich-pilot5-sla.json`
- Full batch **455 doc** chạy nền: log `09_logs/20260629_1334-ai-enrich-full.log`
- `ai_enrich_documents.py` ghi thêm `document_extractions` (deepseek_cleanup) qua `extraction_store.py`

## Sau khi full batch xong

```bash
uv run python scripts/recompute_effective_metadata.py --sync-teable
uv run python scripts/sync_extractions_to_teable.py
```
