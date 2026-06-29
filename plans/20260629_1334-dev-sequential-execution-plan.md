# Plan — DEV chạy lần lượt (Vision → Q&A → Enrich)

**Thời điểm:** 2026-06-29 13:34

## Bước 1 — Vision pilot

| Item | Chi tiết |
|------|----------|
| Script | `scripts/run_vision_ocr_sync.py` |
| Doc mẫu | id=503 (PDF HTH) |
| Blocker | `AI_BOX_VISION_API_KEY` chưa cấu hình |

## Bước 2 — Search Q&A

| Item | Chi tiết |
|------|----------|
| Code | `search_qa.py`, `/api/search/qa` |
| Model | `deepseek-v4-pro` (default group) |
| Giới hạn | Top 10 excerpt, ~3500 chars |

## Bước 3 — AI enrich full

| Item | Chi tiết |
|------|----------|
| Pilot | `--limit 5` → 5/5 OK |
| Full | ~455 doc HTH, `--sleep-seconds 4`, ~3h ước tính |
| SLA | `09_logs/20260629_1334-ai-enrich-full-sla.json` |
| Post | recompute effective + sync Teable extractions |
