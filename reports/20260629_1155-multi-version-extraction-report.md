# Report — Thiết kế & triển khai flow đa phiên bản (priority)

## Bối cảnh

Nhân viên upload văn bản → dùng **AI Webchat + prompt gợi ý** bóc tách → cập nhật **Teable**. Một file có **nhiều phiên bản metadata** với **priority** khác nhau:

**Người > Google Vision > DeepSeek (làm sạch OCR) > OCR local**

## Thiết kế

### Nguyên tắc

1. **Postgres** (`ocr_catalog`) = SoT cho mọi version.
2. **Teable** = UI chỉnh/sửa/xác nhận; mirror versions qua API.
3. Mỗi lần bóc tách = 1 row `document_extractions` (không ghi đè).
4. Bản «đang hiển thị» = `MAX(priority_score)` trong các version `active`/`draft`.

### Bảng Postgres (tổng **6**)

| Bảng | Vai trò |
|------|---------|
| `documents` | File + OCR markdown gốc |
| `document_extractions` | **Mới** — phiên bản metadata theo nguồn |
| `prompt_templates` | **Mới** — prompt gợi ý Webchat |
| `tags`, `categories`, `document_tags` | Facet tìm kiếm |

`document_extractions` chính:

- `source_type`: human_verified | human_webchat | google_vision | deepseek_cleanup | local_llm_ocr
- `priority_score`: 100 / 95 / 70 / 50 / 30
- `version_status`: draft | active | superseded | archived
- `key_fields`, `tags`, `category`, `raw_text`, `extracted_summary`

### Bảng Teable (base **Quản lý Nội bộ** `bsey3ggz3jrRk1sOMqq`)

| Bảng | Table ID | Mô tả |
|------|----------|--------|
| **OwnCloud** | tblNwc8A1llcPa0JcsA | Catalog file (đã có) + **active_priority**, **active_source**, **extraction_version_count** |
| **PromptTemplates** | tbluFFwWvqfWYyngD7r | 3 prompt mẫu (HĐLĐ, QĐ, phạm vi hành nghề) |
| **DocExtractions** | tblnLAXYbsxFtuFhbJa | Mỗi phiên bản bóc tách + **link** → OwnCloud |

Relation: `DocExtractions.document` — **manyOne** → `OwnCloud` (Teable tự tạo link đối xứng).

## Đã triển khai

| Việc | Kết quả |
|------|---------|
| `setup_teable_extraction_schema.py` | 2 bảng mới, 3 field OwnCloud, link, 3 prompt |
| `migrate_document_extractions.py` | Migration + backfill |
| Postgres rows | 470 `local_llm_ocr`, 38 `deepseek_cleanup` |

## API Teable đã dùng (để bạn tắt quyền thừa)

### Giữ cho vận hành hàng ngày

| Method | Endpoint | Mục đích |
|--------|----------|----------|
| GET | `/base/access/all` | Resolve base_id |
| GET | `/base/{baseId}/table` | Liệt kê bảng |
| GET | `/table/{tableId}/field` | Đọc schema |
| GET | `/table/{tableId}/view` | Views |
| GET/POST/PATCH | `/table/{tableId}/record` | Sync & user edit |

### Dùng lúc setup (có thể **tắt** khi schema ổn định)

| Method | Endpoint | Đã dùng |
|--------|----------|---------|
| POST | `/base/{baseId}/table/` | Tạo PromptTemplates, DocExtractions |
| POST | `/table/{tableId}/field` | 13 field catalog + 3 active + link |
| DELETE | `/base/{baseId}/table/{tableId}` | Xóa bảng test |

### Không cần / đã 403

| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `/auth/user/me` | 403 Forbidden |

Audit JSON: `workspace/ocr_pipeline/09_logs/teable-api-permissions-audit.json`

## Flow nhân viên (tóm tắt)

1. Tìm file trên **OwnCloud** (Teable).
2. Mở **PromptTemplates** → copy prompt (VD phạm vi hành nghề).
3. Webchat AI → JSON đề xuất.
4. Lưu row **DocExtractions** (`human_webchat`, draft).
5. Xác nhận → `human_verified` (priority 100) → thắng các bản máy.

## Bước tiếp

1. Script sync `document_extractions` → Teable DocExtractions.
2. Google Vision pipeline → `google_vision` rows.
3. Webhook Teable → Postgres khi user confirm.

## Verdict

Mô hình **multi-version + priority** đã có schema Postgres & Teable; sẵn sàng nối Webchat và Google Vision vào cùng flow.
