# Plan Entry - Low-Cost Search Architecture

## Recommended target architecture (FREE / near-FREE)

1. **Storage layer**: Nextcloud/OwnCloud giữ file gốc.
2. **Catalog layer (SQLite)**:
   - `documents`: `nextcloud_path`, `sha256`, `status`, `markdown`, `doc_json`
   - `tags`, `categories`, bảng nối `document_tags`, `document_categories`
   - `ai_review`, `ai_doc_type`, `ai_key_fields_json` (metadata do AI bổ sung)
3. **Search layer (không dùng AI)**:
   - SQLite FTS5 trên `markdown` + filter tag/category/path/date
   - Tìm kiếm thô trả về top N document id
4. **AI layer (chỉ khi cần)**:
   - Review chất lượng OCR (batch, như hiện tại)
   - Trả lời câu hỏi / trích xuất sâu trên **subset đã lọc** (DeepSeek default group)

## Phased rollout

- **P1 (now)**: path catalog + OCR + tag/category + FTS + webapp list/filter.
- **P2**: sync job từ Nextcloud (theo hash, chỉ OCR file mới/đổi).
- **P3**: Q&A/RAG chỉ trên kết quả tìm kiếm (5–20 tài liệu/lần).

## What to avoid early

- Vector DB trả phí hoặc embed toàn bộ kho ngay từ đầu.
- Gọi LLM cho mọi file chỉ để tạo tag (đốt token không cần thiết).
- Nhân bản binary file vào SQLite.

## Optional upgrade later (still cheap)

- `sqlite-vec` local nếu keyword search chưa đủ.
- Rule-based auto-tag từ tên file/đường dẫn trước khi dùng AI.
