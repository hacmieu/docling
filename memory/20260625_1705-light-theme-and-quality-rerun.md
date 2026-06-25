# Memory Entry - Light Theme and Quality OCR Rerun

- Switched SPA UI to light theme in `workspace/ocr_pipeline/webapp/static/index.html`.
- Re-ran OCR on updated inbox with quality-oriented settings:
  - `easyocr`, languages `vi,en`, confidence `0.25`, `force_full_page_ocr=True`.
- New output DB:
  - `workspace/ocr_pipeline/08_sqlite/memory_tmp_vie_easyocr_quality.db`
- Updated active pointer:
  - `workspace/ocr_pipeline/08_sqlite/ACTIVE_DB.txt`
