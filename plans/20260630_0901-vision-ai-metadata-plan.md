# Plan: Điền ai_* cho Vision trên Teable

**Thời điểm:** 2026-06-30 09:01

## Phân tách lane

| Lane | Việc làm |
|------|----------|
| Google Vision | OCR full text (ảnh/PDF trang 1) |
| DeepSeek enrich | category, doc_type, tags, summary |

Vision **không** tự classify — nhưng metadata enrich đã có trên `documents` từ batch trước.

## Thực hiện

1. `extraction_store.inherit_document_ai_metadata()`
2. Gọi khi persist vision + trước Teable sync
3. Backfill 19 row + resync Teable

## Tương lai (tùy chọn)

Re-enrich trên `raw_text` vision để category chính xác hơn (text sạch hơn EasyOCR).
