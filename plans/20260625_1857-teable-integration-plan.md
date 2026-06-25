# Plan Entry — Teable làm UI quản lý OCR

## PLAN — User tạo trên Teable

### P1. Base & bảng `documents`

| Cột Teable | Kiểu | Nguồn Postgres |
|------------|------|----------------|
| `doc_id` | Number (PK logic) | `documents.id` |
| `owncloud_path` | Long text | `owncloud_path` |
| `file_name` | Formula / text | tách từ path |
| `phong_ban` | Single select | parse từ path hoặc `ai_category` |
| `status` | Single select | `status` |
| `markdown_preview` | Long text | `left(markdown, 2000)` |
| `ocr_duration_s` | Number | `doc_json.ocr_sla.duration_seconds` |
| `ocr_started_at` | DateTime | `doc_json.ocr_sla.started_at` |
| `ocr_finished_at` | DateTime | `doc_json.ocr_sla.finished_at` |
| `ai_category` | Text | `ai_category` |
| `ai_tags` | Long text | `ai_tags` JSON |
| `ai_review` | Long text | `ai_review` |
| `verified_metadata` | Long text | JSON |
| `updated_at` | DateTime | `updated_at` |

Bảng phụ (sau): `tags`, `categories` — hoặc multi-select trên `documents`.

### P2. Views

- `Tất cả — HTH Shared`
- `Chưa OCR` (status = cataloged)
- `Đã OCR` (success)
- `Theo phòng` (group: Truyền Thông / 14.ĐIỀU DƯỠNG / …)

### P3. Credentials (đưa vào `.env`)

```env
TEABLE_API_URL=http://127.0.0.1:3010/api
TEABLE_API_TOKEN=...
TEABLE_BASE_ID=...
TEABLE_TABLE_DOCUMENTS_ID=...
```

### P4. Script sync (repo — bước kế)

`scripts/sync_catalog_to_teable.py`:
- Đọc Postgres (`documents` đã OCR / mới)
- Upsert qua `POST/PATCH /api/table/{tableId}/record`
- Key upsert: `doc_id` hoặc `owncloud_path`

### P5. Quy trình vận hành

1. Upload OCIS → `owncloud_sync_catalog.py --prune-missing`
2. OCR → `ocr_catalog_postgres.py`
3. AI → `ai_enrich_documents.py`
4. **Sync Teable** → user xem/lọc trên Teable, không cần `pg_app.py` hàng ngày

## CHECK

- [ ] Base + bảng tạo xong trên Teable
- [ ] Token API hoạt động (`curl` list records)
- [ ] Script sync đẩy ≥10 row pilot khớp Postgres
- [ ] View lọc tiếng Việt hiển thị đúng tên file

## Lưu ý

- Không ghi trực tiếp vào Postgres Teable (5432) — chỉ API.
- Postgres `ocr_catalog` (5433) vẫn là SoT cho pipeline/AI.
