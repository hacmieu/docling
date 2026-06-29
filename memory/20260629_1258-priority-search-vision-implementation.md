# Memory — Triển khai waterfall, search staff, Celery Vision

**Thời điểm:** 2026-06-29 12:58

## Đã làm

1. **Migration 005** — cache `effective_*` trên `documents` (470 row có extraction, 28 cleared).
2. **`recompute_effective_metadata.py`** — recompute Postgres + PATCH Teable `active_priority`, `active_source`, `extraction_version_count`.
3. **Dọn OwnCloud Teable** — xóa `ai_category`, `ai_doc_type`, `ai_tags` (và `ai_review` trước đó); `_link_child_test` đã không còn trên server.
4. **`concept_search.py` + `/api/search`** — concept map `concepts_vi.json`, FTS markdown + tag/category từ `effective_document_extractions`.
5. **Celery** — `celery_app.py`, `tasks/vision_tasks.py` (Gemini `AI_BOX_VISION_API_KEY`), `enqueue_vision_ocr.py`; Redis port 6379 đã có sẵn trên host (container `ocr-redis` bind conflict — dùng Redis hiện có).

## Chạy worker

```bash
uv run celery -A workspace.ocr_pipeline.celery_app worker -Q vision -c 1
uv run python scripts/enqueue_vision_ocr.py --doc-id 123
```

## Ghi chú

- Metadata AI trên OwnCloud chuyển sang bảng **DocExtractions** + lookup; OwnCloud chỉ giữ path, OCR preview, SLA, `active_*`.
- Search mẫu «phạm vi hành nghề» trên `project/hth-shared-drive` trả ~27 hit (synonym `phạm vi`).
