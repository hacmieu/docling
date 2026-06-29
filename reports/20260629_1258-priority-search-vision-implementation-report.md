# Report — Triển khai waterfall, search, Celery Vision

**Thời điểm:** 2026-06-29 12:58

## Kết quả

| Hạng mục | Trạng thái | Chi tiết |
|----------|------------|----------|
| Postgres effective cache | ✅ | 470 updated, 28 cleared |
| Teable dọn field | ✅ | Xóa ai_category, ai_doc_type, ai_tags; ai_review đã xóa trước đó |
| Teable PATCH active_* | ✅ | 475 patched, 0 skipped |
| `/api/search` | ✅ | Concept «phạm vi hành nghề» → 5+ hit trên HTH drive (sau fix param order) |
| Celery + vision task | ✅ | Code + deps; Redis host sẵn có |
| Docker ocr-redis | ⚠️ | Port 6379 đã chiếm — không start container mới |

## File mới / đổi chính

- `scripts/recompute_effective_metadata.py`
- `scripts/cleanup_teable_owncloud_fields.py`
- `scripts/enqueue_vision_ocr.py`
- `workspace/ocr_pipeline/concept_search.py`
- `workspace/ocr_pipeline/config/concepts_vi.json`
- `workspace/ocr_pipeline/celery_app.py`
- `workspace/ocr_pipeline/tasks/vision_tasks.py`
- `workspace/ocr_pipeline/webapp/pg_app.py` — `/api/search`
- `workspace/ocr_pipeline/teable_catalog.py` — slim fields
- `infra/postgres/migrations/005_documents_effective_cache.sql`
- `infra/docker-compose.yml` — service `ocr-redis`
- `requirements-pipeline.txt` — celery, redis, requests, pypdfium2

## Kiểm thử nhanh

```bash
uv run python scripts/recompute_effective_metadata.py
uv run python -c "from workspace.ocr_pipeline.webapp.pg_app import PgCatalogDb; from workspace.ocr_pipeline.db_postgres import load_dotenv; load_dotenv(); print(PgCatalogDb().search_documents('phạm vi hành nghề', 5, 'project/hth-shared-drive', None)['total'])"
curl -s 'http://127.0.0.1:8766/api/search?q=phạm+vi+hành+nghề&drive=project/hth-shared-drive' | head
```

## Rủi ro / follow-up

- Vision worker chưa chạy production; cần validate Gemini key và rate limit 10/m.
- Sau cleanup Teable, chạy `sync_catalog_to_teable.py` nếu cần refresh toàn bộ row (không chỉ active_*).
