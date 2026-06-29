# Plan — Rollout Google Gemini Vision (free-tier)

1. Giữ lane text trên AI Box (`AI_BOX_API_KEY` / DeepSeek).
2. Dùng lane vision riêng qua Google:
   - `GOOGLE_API_KEY`
   - `GOOGLE_VISION_MODEL=gemini-2.5-flash` (có thể đổi `gemini-2.5-pro` khi cần chất lượng cao hơn).
3. Chạy vision batch thật chậm để phù hợp free-tier:
   - `uv run python scripts/run_vision_batch_sync.py --sleep-seconds 12`
4. Sau mỗi đợt vision:
   - `uv run python scripts/recompute_effective_metadata.py --sync-teable`
   - `uv run python scripts/sync_extractions_to_teable.py`
