# Plan — Thực thi P1–P3 (waterfall, search, vision queue)

**Thời điểm:** 2026-06-29 12:58  
**Nguồn:** [20260629_1250-priority-search-vision-plan.md](./20260629_1250-priority-search-vision-plan.md)

## P1 — OwnCloud + effective cache ✅

| Bước | Script / file |
|------|----------------|
| Migration 005 | `infra/postgres/migrations/005_documents_effective_cache.sql` |
| Recompute Postgres | `scripts/recompute_effective_metadata.py` |
| Dọn field thừa | `scripts/cleanup_teable_owncloud_fields.py` |
| Sync catalog slim | `teable_catalog.build_record_fields` (bỏ ai_*) |

## P2 — Staff search ✅

| Bước | File |
|------|------|
| Concept registry | `config/concepts_vi.json` |
| Search SQL | `concept_search.py` |
| HTTP API | `GET /api/search?q=...&drive=...&phong_ban=...` trong `pg_app.py` |

## P3 — Celery Vision ✅ (hạ tầng)

| Bước | File |
|------|------|
| Broker | Redis (host :6379 hoặc `CELERY_BROKER_URL`) |
| App | `workspace/ocr_pipeline/celery_app.py` |
| Task | `tasks/vision_tasks.py` → `google_vision` extraction |
| Enqueue CLI | `scripts/enqueue_vision_ocr.py` |

## Còn lại (ngoài scope lần này)

- [ ] Pilot enqueue 1–5 doc vision thật (cần `AI_BOX_VISION_API_KEY` + worker chạy).
- [ ] DeepSeek Q&A trên top-10 excerpt (P2 optional).
- [ ] Full `ai_enrich_documents.py` batch ~439 doc.
