# Plan: Multi-format ingest → markdown (đã thực hiện)

## Mục tiêu

Mọi định dạng trong `PIPELINE_INGEST_EXTENSIONS` được tải từ OCIS, convert Docling, ghi `documents.markdown` + `local_llm_ocr`, rồi enrich lane 1.

## Routing (đã cấu hình)

| Loại | Strategy | Engine |
|------|----------|--------|
| `.docx` | `docling_parse` | DocumentConverter native |
| `.jpg` | `docling_ocr` | EasyOCR vi,en |
| `.m4a` | `asr` | Chưa trong allowlist — skip |

## Các bước đã chạy

1. [x] Hoàn thiện `upsert_local_llm_ocr_from_markdown`
2. [x] Sửa `select_documents` suffix routing
3. [x] Pilot docx id=533
4. [x] Batch `--all` 26 file còn lại
5. [x] Re-enrich 27 doc `--force`
6. [ ] Audio doc 991 (cần bật ASR extra)
7. [ ] Vision + Teable sync cho ảnh mới

## Lệnh tham chiếu

```bash
uv run python scripts/ocr_catalog_postgres.py --all \
  --sla-report workspace/ocr_pipeline/09_logs/20260630_1025-multi-format-ingest-full.json

for id in ...; do
  uv run python scripts/ai_enrich_documents.py --doc-id "$id" --force
done
```
