# Multi-format ingest — triển khai

**Thời điểm:** 2026-06-30 10:40 (local)

## Code hoàn thiện

- `workspace/ocr_pipeline/extraction_store.py`: `upsert_local_llm_ocr_from_markdown` — ghi RAW lane sau ingest.
- `scripts/ocr_catalog_postgres.py`: multi-format (`--only-pdf` mặc định false), converter cache theo strategy, fix `strategy_for_suffix(suffix_from_path(path))`.
- `workspace/ocr_pipeline/ingest_converter.py` + `ingest_formats.py` đã nối vào catalog script.

## Batch ingest

| Metric | Giá trị |
|--------|---------|
| Cataloged trước batch | 28 (21 jpg, 6 docx, 1 m4a) |
| Ingest thành công | **27/27** (docx 6 + jpg 21; doc 533 pilot riêng) |
| Thời gian batch | 205s (~3.4 phút) |
| Còn cataloged | **1** — doc 991 `.m4a` (ngoài `PIPELINE_INGEST_EXTENSIONS`) |
| SLA log | `workspace/ocr_pipeline/09_logs/20260630_1025-multi-format-ingest-full.json` |

## AI enrich lane 1

- Re-enrich `--force` 27 doc có markdown mới (deepseek_cleanup cũ từ lúc chưa có OCR).
- Doc IDs: 533,599,728,747,754–761,776,811,831–837,843,934,983,987,988,1378.
- Log tổng: `workspace/ocr_pipeline/09_logs/20260630_1030-multi-format-enrich.log`

## Lỗi đã sửa trong phiên

1. `strategy_for_suffix(path)` truyền full path → luôn `None`.
2. Thiếu import `STRATEGY_DOCLING_PARSE` → ingest fail sau convert.

## Tiếp theo (tùy chọn)

- Thêm `.m4a` + `PIPELINE_INGEST_AUDIO_STRATEGY=asr` + extra Docling ASR cho doc 991.
- Vision lane trên ảnh mới ingest (batch vision hoặc per-doc).
- Teable sync cho extraction mới.
