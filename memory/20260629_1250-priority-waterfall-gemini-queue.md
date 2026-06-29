# Memory — Priority waterfall, field thừa OwnCloud, Gemini queue

## Priority (đã sửa hiểu đúng)

**Không** chọn row `version_status=active` tùy tiện. **Waterfall theo điểm:**

1. Lọc bỏ `archived`, `superseded`
2. Chọn row **priority_score cao nhất còn tồn tại**
3. Không có human → dùng google_vision → deepseek → RAW OCR

View Postgres: `effective_document_extractions`  
Code: `extraction_priority.resolve_effective_extraction()`

## Field thừa trên OwnCloud (sau tách DocExtractions)

| Field | Khuyến nghị |
|-------|-------------|
| ai_category, ai_doc_type, ai_tags | **Thừa** → lookup từ effective extraction hoặc xóa |
| ai_review | **Thừa** → nằm trong DocExtractions.extracted_summary |
| _link_child_test | **Xóa** (rác test) |
| markdown_preview | Giữ tạm cho search; lâu dài lấy từ RAW extraction |
| active_priority, active_source | Giữ nếu **sync computed** từ waterfall |

## Gemini + Celery

- Key vision **tách** `AI_BOX_VISION_API_KEY` — chỉ `gemini-3-flash` đọc ảnh
- DeepSeek text chat giữ key hiện tại
- Hàng đợi Celery + Redis, rate limit tránh 429
