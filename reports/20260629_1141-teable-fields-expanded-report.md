# Report — Mở rộng Teable fields + full resync

## Yêu cầu

User bật API thêm/sửa/xóa tables & fields → tiếp tục triển khai catalog đầy đủ lên Teable noibo.

## Thực hiện

### 1. Tạo field qua API

`scripts/setup_teable_catalog_fields.py` — 13 cột mới:

| Field | Type | Nguồn |
|-------|------|-------|
| owncloud_path | longText | path NFC |
| file_name | singleLineText | basename |
| phong_ban | singleLineText | segment sau drive prefix |
| catalog_status | singleLineText | documents.status |
| markdown_preview | longText | markdown[:2000] |
| ocr_duration_s | number | doc_json.ocr_sla |
| ocr_started_at / ocr_finished_at | singleLineText | ISO SLA |
| ai_category, ai_doc_type | singleLineText | AI enrich |
| ai_tags, ai_review | longText | AI enrich |
| updated_at | singleLineText | Postgres |

### 2. Sync mở rộng

`scripts/sync_catalog_to_teable.py --ensure-fields` — upsert 16 field/record.

### 3. Kết quả

| Metric | Giá trị |
|--------|---------|
| Fields created | 13 |
| Records updated | **475/475** |
| Failed | 0 |
| Duration | ~227s |

### 4. Kiểm tra mẫu (doc_id 503)

- `phong_ban`: Truyền Thông
- `ai_category`: Hợp đồng lao động
- `markdown_preview`: có nội dung OCR tiếng Việt
- `ocr_duration_s`: 17.044

## Files mới

- `workspace/ocr_pipeline/teable_catalog.py`
- `scripts/setup_teable_catalog_fields.py`

## Verdict

Teable OwnCloud **đủ cột** để nhân viên lọc/tìm theo path, phòng ban, OCR text preview và AI tags — sẵn sàng tạo Views trên UI Teable.
