# Báo cáo triển khai multi-format ingest

**Ngày:** 2026-06-30

## Tóm tắt

Đã triển khai ingest đa định dạng trên pipeline Postgres: **27/28** file cataloged non-PDF chuyển sang `success` với markdown và extraction `local_llm_ocr`. Một file audio `.m4a` (id 991) giữ `cataloged` vì chưa nằm trong allowlist.

## Kết quả ingest

| Strategy | Số file | Thành công |
|----------|---------|------------|
| `docling_parse` (docx) | 6 | 6 |
| `docling_ocr` (jpg) | 21 | 21 |
| **Tổng** | **27** | **27** |

- Thời gian trung bình: **7.9s/file** (ảnh scan chậm nhất ~35s).
- Postgres: **497 success**, **1 cataloged** (m4a).

## AI enrich

27 document được re-enrich từ markdown thật (trước đó enrich khi markdown rỗng). Ví dụ doc 934: category `lao động`, summary hợp đồng lao động đầy đủ.

## Artifact

- Ingest SLA: `workspace/ocr_pipeline/09_logs/20260630_1025-multi-format-ingest-full.json`
- Enrich log: `workspace/ocr_pipeline/09_logs/20260630_1030-multi-format-enrich.log`

## Ghi chú vận hành

- Mặc định `ocr_catalog_postgres.py` không còn `--only-pdf`; dùng `PIPELINE_INGEST_EXTENSIONS`.
- Sau ingest cần `--force` enrich nếu doc đã có `ai_review_status=success` từ lần catalog trước.
