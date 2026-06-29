# Report — Tổng kết + DEV song song

**Thời điểm:** 2026-06-29 14:16

## Bảng tiến độ

| Hạng mục | Kết quả |
|----------|---------|
| OCR local (EasyOCR) | ✅ ~447 PDF HTH |
| Postgres + Teable sync | ✅ 475 doc, DocExtractions ~462 |
| Waterfall + search + Q&A | ✅ code + Teable PATCH |
| DeepSeek enrich full | 🔄 ~80+ processed (log), batch nền từ 13:40 |
| Gemini vision batch | ⚠️ pilot 403 — thiếu **Codex** key |
| Commit per doc enrich | ✅ fix trong `ai_enrich_documents.py` |
| `run_vision_batch_sync.py` | ✅ mới — sẵn sàng khi có key |

## Gemini pilot

```
doc_id=503 → 403 Forbidden (gemini-3-flash + default-group key)
```

**Hành động:** tạo API key nhóm Codex trên ai-box.vn → `AI_BOX_VISION_API_KEY` trong `.env` → chạy batch song song enrich.

## File mới lần này

- `scripts/run_vision_batch_sync.py`
- Fix: `ai_enrich_documents.py` (`conn.commit()` mỗi doc)
- Fix: `vision_tasks.py` (DEV fallback key nếu cần)

## Theo dõi enrich

```bash
grep -c '^\[OK\]' workspace/ocr_pipeline/09_logs/20260629_1334-ai-enrich-full.log
tail -f workspace/ocr_pipeline/09_logs/20260629_1334-ai-enrich-full.log
```
