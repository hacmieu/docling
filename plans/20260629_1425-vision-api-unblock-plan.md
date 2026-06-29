# Plan — Chạy Gemini sau khi kênh API sẵn sàng

**Thời điểm:** 2026-06-29 14:25

## Trạng thái

- `AI_BOX_VISION_API_KEY` trong `.env`: ✅ token riêng (≠ `AI_BOX_API_KEY`)
- Code batch: ✅ `run_vision_batch_sync.py`
- Blocker hiện tại: AI Box trả 503 — không có kênh distributor cho `gemini-3-flash`

## Khi `check_vision_api.py` pass

```bash
# Song song với enrich
uv run python scripts/run_vision_batch_sync.py --sleep-seconds 6 \
  --log-file workspace/ocr_pipeline/09_logs/20260629_vision-batch.log
```

## Post-sync (sau enrich + vision)

```bash
uv run python scripts/recompute_effective_metadata.py --sync-teable
uv run python scripts/sync_extractions_to_teable.py
```
