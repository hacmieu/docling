# Memory Entry - AI Review with DeepSeek Default Group

- Provider policy applied: use default-group API key for text/chat (DeepSeek), not Codex (10 RPM, image models).
- Avoid `gemini-3-flash` for text review (image-only per provider).
- Switched `AI_BOX_MODEL` to `deepseek-v4-pro` in `.env` / `.env.example`.
- Added `scripts/ai_review_sqlite.py` and SQLite columns: `ai_review`, `ai_review_status`, `ai_review_at`, `ai_review_model`, `ai_review_error`.
- Final run: 23/23 documents `ai_review_status=success` (19 deepseek-v4-pro, 4 legacy gemini-3-flash from earlier test).
