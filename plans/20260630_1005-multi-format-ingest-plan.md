# Plan: Xử lý Word / Excel / Ảnh — hội tụ Markdown

**Thời điểm:** 2026-06-30 10:05

## Nguyên tắc

**Mọi định dạng đều hội tụ về `documents.markdown`** (text layer chuẩn). Từ markdown fork ra:
- `local_llm_ocr` extraction (RAW)
- `deepseek_cleanup` (AI metadata)
- `google_vision` / vision lane (nếu áp dụng)

Teable, search, enrich đều đọc từ text layer + extractions — không lưu binary Office làm SoT.

## Routing theo loại file

| Loại | Chiến lược mặc định | VAR | Ghi chú |
|------|---------------------|-----|---------|
| PDF | `docling_ocr` | `PIPELINE_INGEST_PDF_STRATEGY` | Docling+EasyOCR → md; vision tùy chọn |
| DOCX | `docling_parse` | `PIPELINE_INGEST_DOCX_STRATEGY` | Parse cấu trúc Word, **không OCR ảnh** |
| XLSX | `docling_parse` | `PIPELINE_INGEST_XLSX_STRATEGY` | Bảng → markdown |
| PPTX | `docling_parse` | `PIPELINE_INGEST_PPTX_STRATEGY` | Slide → markdown |
| JPG/PNG | `docling_ocr` | `PIPELINE_INGEST_IMAGE_STRATEGY` | OCR ảnh; vision đọc file trực tiếp |
| M4A/MP3 | `asr` | `PIPELINE_INGEST_AUDIO_STRATEGY` | Docling ASR extra (phase sau) |

Allowlist: `PIPELINE_INGEST_EXTENSIONS`

## Hiện trạng catalog HTH

| ext | status | count |
|-----|--------|------:|
| .pdf | success | 463 |
| .jpg | cataloged | 21 |
| .jpg | success | 7 |
| .docx | cataloged | 6 |
| .m4a | cataloged | 1 |

`ocr_catalog_postgres.py` mặc định `--only-pdf` → 28 file non-PDF chưa ingest.

## Bước triển khai

1. ✅ `ingest_formats.py` — SSOT routing + VAR
2. ⏳ Mở rộng `ocr_catalog_postgres.py`: filter theo `load_ingest_extensions()`, strategy `docling_parse` vs `docling_ocr`
3. ⏳ Vision: đã hỗ trợ ảnh; thêm render DOCX→PDF cho lane vision (tùy chọn)
4. ⏳ Pilot: `--only-pdf false` + 6 docx + 21 jpg cataloged

## Lệnh pilot (sau bước 2)

```bash
# Office + ảnh → markdown
uv run python scripts/ocr_catalog_postgres.py --all --no-only-pdf
```
