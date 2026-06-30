# Fix DeepSeek synthesize — context preview + tokens trước

**Ngày:** 2026-06-30 23:08

## Triệu chứng

Model trả "Tôi cần một câu hỏi cụ thể…" dù footer ~811 tokens — user không thấy context trước khi gửi.

## Nguyên nhân

1. UI không hiển thị `llm_prompt_block` — khó biết dữ liệu có vào prompt không
2. Prompt cũ lồng "Câu hỏi" trong block + system message yếu → model đôi khi bỏ qua metadata
3. Có thể gửi khi chưa Tìm kiếm (context rỗng)

## Sửa

- `search.html`: panel tokens trước gửi, textarea context chỉnh sửa, checkbox chọn doc
- `search_qa.py`: prompt rõ "BẮT BUỘC trả lời từ DỮ LIỆU CATALOG", validate doc_count/context
- `llm_context_pack`: block metadata không trùng câu hỏi user

## Dùng lại

Hard refresh `/search` → Tìm kiếm → xem context + ~tokens → Gửi DeepSeek
