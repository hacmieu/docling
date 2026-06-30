# Báo cáo: Điền ai_category / ai_tags cho Vision trên Teable

**Thời điểm:** 2026-06-30 09:01

## Nguyên nhân cột trống

Google Vision lane chỉ ghi **OCR text** vào `document_extractions`. Các cột `ai_category`, `ai_doc_type`, `ai_tags` trên Teable DocExtractions lấy từ **cùng bảng Postgres** — trong khi enrich DeepSeek ghi metadata vào row `deepseek_cleanup` và `documents`, không tự copy sang `google_vision`.

## Cách xử lý

Khi tạo/sync Vision extraction → **kế thừa** metadata từ:

1. `documents.ai_category`, `ai_doc_type`, `ai_tags`, `ai_key_fields`, `ai_review`
2. Hoặc row `deepseek_cleanup` nếu documents trống

Sau đó PATCH Teable như bình thường.

## Backfill

| Hạng mục | Kết quả |
|----------|---------|
| Vision row thiếu metadata | 19 |
| Inherited | **19/19** |
| Teable resync | **19/19 OK** |

Refresh Teable — các dòng `Vision-v*` sẽ có `ai_category`, `ai_doc_type`, `ai_tags` giống DeepSeek-v* cùng document.

## Doc mới trong batch

Batch vision đang chạy tự inherit + sync — không cần thao tác thêm.
