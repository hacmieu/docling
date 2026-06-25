# Memory — AI category / tag / label cho catalog OCR

## Câu hỏi

User hỏi: dùng AI xếp nội dung vào **category** và **tag** có ổn không? Trước đây đã có **API tìm email theo luồng, ngày tháng** để làm context cho AI.

## Kết luận ngắn

**Có — ổn và đúng hướng**, nhưng **không thay** API lọc theo luồng/thời gian/đường dẫn. Hai lớp bổ sung nhau:

| Lớp | Vai trò | Chi phí |
|-----|---------|---------|
| **Structural context API** (giống email) | Lọc theo phòng ban (path), ngày upload/OCR, luồng hồ sơ, sha256 | Gần như 0 |
| **Category + tag (AI)** | Phân loại ngữ nghĩa, facet tìm kiếm, tóm tắt | 1 lần/doc (batch) |
| **FTS markdown** | Từ khóa trong OCR | 0 khi query |
| **AI Q&A** | Chỉ trên subset đã lọc (5–20 doc) | Theo câu hỏi |

## Đã có trong repo

- `scripts/ai_enrich_documents.py` → `ai_category`, `ai_tags`, `ai_doc_type`, `ai_key_fields`, `ai_ocr_quality`
- Bảng `tags`, `categories`, `document_tags` + `verified_metadata` cho con người sửa
- Kiến trúc low-cost: [plans/20260625_1743-low-cost-search-architecture-plan.md](../plans/20260625_1743-low-cost-search-architecture-plan.md)

## Mapping từ mô hình email

- **Luồng (thread)** → folder OCIS / case id / `related_document_ids` (tương lai)
- **Ngày** → `updated_at`, `verified_at`, `ai_key_fields.ngay`
- **Phòng ban** → prefix `owncloud_path` (rule-based, không cần AI)
- **Tag/category** → AI đọc OCR, gán facet để tìm nhanh trước khi đưa markdown vào prompt

## Bước tiếp

1. Chuẩn hóa taxonomy gợi ý (10–15 category, tag tự do có normalize).
2. Rule tag từ path trước AI enrich.
3. Chạy enrich batch ~447 PDF đã OCR (`--sleep-seconds 6`).
4. API context: filter structural → trả metadata + excerpt markdown cho LLM (pattern email cũ).
