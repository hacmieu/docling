# Plan — Gemini Codex retry

1. Giữ `AI_BOX_VISION_API_KEY` hiện tại (đã có quyền model).
2. Gọi `gemini-3-flash` với nhịp chậm (sleep/backoff) để tránh 429.
3. Khi có response `200` ổn định, chạy lane vision batch song song với enrich:
   - `uv run python scripts/run_vision_batch_sync.py --sleep-seconds 6`
4. Sau khi lane enrich + vision hoàn tất:
   - `uv run python scripts/recompute_effective_metadata.py --sync-teable`
   - `uv run python scripts/sync_extractions_to_teable.py`
