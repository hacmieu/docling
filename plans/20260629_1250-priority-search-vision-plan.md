# Plan — Priority waterfall, dọn OwnCloud, search staff, Celery Vision

## P0 — Priority waterfall (done code/SQL)

```sql
-- effective row per document
SELECT * FROM effective_document_extractions WHERE document_id = $1;
```

`version_status`: `draft` vẫn được fallback nếu là tier cao nhất; chỉ `archived`/`superseded` bị loại.

## P1 — Dọn OwnCloud Teable

| Action | Field |
|--------|-------|
| DELETE | `_link_child_test` |
| DELETE hoặc → Lookup | `ai_category`, `ai_doc_type`, `ai_tags`, `ai_review` |
| Lookup từ DocExtractions | `effective_category`, `effective_source` (thay active_*) |

Sync job: `recompute_owncloud_effective.py` PATCH `active_priority`, `active_source` từ view.

## P2 — Staff search («phạm vi hành nghề»)

```
Query user
  → concept map (synonyms)
  → FTS documents.markdown + effective_extractions.tags/category
  → filter phong_ban, date
  → list OwnCloud rows + link DocExtractions
  → optional DeepSeek Q&A trên top 10 excerpt
```

Teable: View filter `effective` lookup; search trên `markdown_preview` + linked extraction tags.

## P3 — Celery Vision queue (Gemini)

```
Upload/scan image PDF page
  → enqueue vision_tasks.ocr_page(doc_id, page_no)
  → worker: gemini-3-flash (AI_BOX_VISION_API_KEY)
  → INSERT document_extractions source_type=google_vision priority=70
  → normalize → sync Teable
```

| Component | Ghi chú |
|-----------|---------|
| Broker | Redis `CELERY_BROKER_URL` |
| Rate | `CELERY_VISION_RATE_LIMIT=10/m` + exponential backoff 429 |
| Model | `gemini-3-flash` **chỉ ảnh** |
| Text | DeepSeek `AI_BOX_API_KEY` — không dùng Gemini |

Files đề xuất: `workspace/ocr_pipeline/tasks/vision_tasks.py`, `celery_app.py`

## Quan hệ bảng (target)

```
documents 1──* document_extractions
documents *──* tags (via document_tags, từ effective extraction)
prompt_templates 1──* document_extractions (optional)

Teable:
  OwnCloud 1──* DocExtractions (link)
  PromptTemplates (standalone)
```
