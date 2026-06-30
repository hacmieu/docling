# Memory: Đa định dạng → Markdown

**Thời điểm:** 2026-06-30 10:05

- SoT text: **`documents.markdown`** cho mọi loại file.
- Office (docx/xlsx): **Docling parse** — đọc cấu trúc, không cần OCR bitmap.
- Ảnh/PDF: **Docling OCR** (lane RAW) và/hoặc **Vision** (lane 2).
- Module `ingest_formats.py` + VAR `PIPELINE_INGEST_*`.
- Catalog HTH: 28 file chưa OCR (21 jpg, 6 docx, 1 m4a) do batch chỉ chạy PDF.
