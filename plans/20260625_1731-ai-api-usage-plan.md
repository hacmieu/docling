# Plan Entry - AI API Usage Policy

## Key rules (ai-box.vn)

1. Default group + DeepSeek (or other text models) for OCR markdown review.
2. Codex group: ~10 RPM, reserved for image-reading models; use a separate API key if needed.
3. Do not use `gemini-3-flash` / `gemini-3-flash-thinking` for chat/text API.

## Operational command

```bash
uv run python scripts/ai_review_sqlite.py --sleep-seconds 6
```

Stop the webapp while batch review runs to avoid SQLite lock conflicts.
