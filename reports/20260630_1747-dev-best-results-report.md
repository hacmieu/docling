# Báo cáo DEV — kết quả tốt nhất

**Ngày:** 2026-06-30

## Tóm tắt

| Hạng mục | Trạng thái |
|----------|------------|
| Documents Postgres | 498/498 success |
| Vision 21 JPG mới | **21/21** có `google_vision` |
| Teable DocExtractions ERD | **Ready** |
| Teable OwnCloud ERD | Gần ready (1 orphan link) |
| Effective metadata cache | 498/498 |

## Vision

- Batch tuần tự `sleep 60s` đã chạy ~33 phút cho 21 ảnh.
- Cải thiện API: timeout 300s, retry 503/timeout, resize max edge 2048px.
- Doc 831 hoàn tất sau retry (~396s).

## Teable chuẩn ERD

**OwnCloud (canonical):** Label, Number, Status, path/file/phòng ban, markdown_preview, OCR SLA, active_priority/source, extraction_version_count, DocExtractions link.

**DocExtractions (canonical):** version_label, postgres_extraction_id, doc_id, source_type, priority, ai_*, summary, raw preview, document link.

**Không chuẩn:** `_link_child_test` — orphan, cần xóa thủ công trên Teable.

## Khuyến nghị báo cáo/tìm kiếm

- Filter OwnCloud theo `phong_ban`, `active_source`, `Status`.
- Tra cứu metadata AI qua link **DocExtractions** hoặc view `effective_document_extractions` trên Postgres.
