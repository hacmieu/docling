# Memory: Kế thừa AI metadata cho Vision extraction

**Thời điểm:** 2026-06-30 09:01

## Vấn đề

Vision OCR (Gemini) chỉ lưu `raw_text`; cột Teable `ai_category`, `ai_doc_type`, `ai_tags` trống dù DeepSeek enrich đã chạy trên `documents`.

## Giải pháp

`inherit_document_ai_metadata()` — copy từ `documents.ai_*` (fallback `deepseek_cleanup`) sang row `google_vision` trước khi sync Teable.

Gọi tại:
- `persist_vision_extraction()` (doc mới)
- `sync_extraction_and_document()` (an toàn khi sync)
- `backfill_vision_ai_metadata.py` (19 doc đã OCR)

## Kết quả backfill

19/19 inherited + Teable resync OK. Ví dụ doc 503: Vision row có `Hợp đồng lao động`, tags đầy đủ.
