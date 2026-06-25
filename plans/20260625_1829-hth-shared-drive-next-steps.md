# Plan Entry — Bước tiếp sau HTH-Shared-Drive

## Đã xong

- [x] Project Space `project/hth-shared-drive` trên OCIS
- [x] Sync catalog → Postgres (491 file)

## CHECKLIST tiếp theo

| # | Bước | Lệnh / việc |
|---|------|-------------|
| 1 | Chuẩn hóa thư mục phòng ban | Đổi `Truyền Thông/` → tên phòng (02-CDHA, 05-To-chuc-can-bo…) nếu cần |
| 2 | Sync lại sau upload mới | `owncloud_sync_catalog.py --drive-alias project/hth-shared-drive` |
| 3 | **OCR từ OCIS** | Script tải PDF qua WebDAV → Docling → cập nhật `markdown` (chưa có — bước kế) |
| 4 | AI enrich | `ai_enrich_documents.py --sleep-seconds 6` (sau khi có markdown) |
| 5 | Tra cứu | Query Postgres FTS / webapp |

## Pilot OCR (thủ công tạm)

Tải 1 PDF từ OCIS → `workspace/ocr_pipeline/01_inbox/` → `folder_to_sqlite_mvp.py` để thử chất lượng trước batch 491 file.
