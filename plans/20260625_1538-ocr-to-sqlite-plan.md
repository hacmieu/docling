# Plan Entry - OCR to SQLite Temporary Memory

## Trial flow

1. Convert input with Docling (`DocumentConverter` + OCR options for scanned docs).
2. Export both Markdown and structured JSON.
3. Insert into SQLite with a simple schema:
   - documents(id, source, sha256, markdown, doc_json, created_at, status)
4. Query from SQLite for downstream retrieval or chunking.

## Operational guidance

- For scanned PDFs/images, enable OCR explicitly (`PdfPipelineOptions.do_ocr = True`).
- For mostly digital PDFs, avoid forcing full-page OCR unless needed.
- Keep original files plus deterministic hashes for idempotent upserts.
