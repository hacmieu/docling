# Báo cáo — Tìm kiếm sâu + gói ngữ cảnh cho LLM (có tính tokens)

**Ngày:** 2026-06-30

## Có dữ liệu tìm sâu chưa?

**Có — ở mức metadata + summary**, đủ để lọc trước và đưa vào LLM mà không quét 498 file markdown.

| Chỉ số DEV | Giá trị |
|------------|---------|
| Doc success | 498 |
| Có `key_fields` | 474 |
| Có `doc_type` | 475 |
| Vision enrich DeepSeek | 40/40 |

**Hạn chế:** một số doc RAW (PDF) vẫn dùng schema enrich cũ (`ten/so/ngay/don_vi`); lane vision/staff JPG đã có field chi tiết hơn (CCCD: `so_cccd`, `ngay_sinh`…).

---

## Ví dụ 1 — Trần Đức Hiển (7 tài liệu)

```bash
uv run python scripts/export_llm_context.py staff "Trần Đức Hiển" \
  -o workspace/ocr_pipeline/07_exports/tran-duc-hien-llm-pack.json
```

**Kết quả:** 7 doc (831–837), **~720 tokens** (`llm_prompt_block`).

| doc_id | doc_type | Ghi chú |
|--------|----------|---------|
| 831 | can-cuoc-cong-dan | Mặt sau CCCD (OCR tên khác — vẫn trong folder) |
| 832 | can-cuoc-cong-dan | CCCD Trần Đức Hiển |
| 833 | ban-sao-bang-cap | Bằng Bác sĩ Y đa khoa |
| 834–836 | chung-chi* | Đào tạo liên tục |
| 837 | chung-chi-hanh-nghe | CCHN đa khoa |

**SQL tương đương:**

```sql
SELECT d.id, e.doc_type, e.key_fields, e.extracted_summary
FROM documents d
JOIN effective_document_extractions e ON e.document_id = d.id
WHERE d.id BETWEEN 831 AND 837;
```

---

## Ví dụ 2 — Bằng cấp / chứng chỉ bác sĩ

```bash
uv run python scripts/export_llm_context.py degrees --all-catalog --limit 200
```

**Kết quả DEV:** **66** tài liệu loại bằng/chứng chỉ, **~7.268 tokens** prompt (metadata + summary ngắn, không full OCR).

Phân loại: `bang-tot-nghiep` (13), `chung-chi` (19), `chung-chi-hanh-nghe` (5), …

**SQL:**

```sql
SELECT * FROM document_certificate_status
WHERE doc_type LIKE 'bang%' OR doc_type LIKE 'chung-chi%';
```

---

## Định dạng output cho LLM (có tính tokens)

File JSON export gồm:

```json
{
  "query": "Tất cả thông tin của Trần Đức Hiển",
  "doc_count": 7,
  "estimated_tokens_json": 850,
  "estimated_tokens_prompt": 720,
  "llm_prompt_block": "Câu hỏi: ...\n[doc_id=832] type=can-cuoc-cong-dan\nkey_fields={...}\nsummary=...",
  "documents": [
    {
      "doc_id": 832,
      "doc_type": "can-cuoc-cong-dan",
      "key_fields": { "ten": "Trần Đức Hiển", "so": "015092000693", ... },
      "summary": "...",
      "path_tail": "BÁC SĨ/.../CCCD.jpg"
    }
  ]
}
```

- **`estimated_tokens_prompt`**: ước lượng tokens khi paste `llm_prompt_block` vào LLM (~chars/4).
- **`estimated_tokens_json`**: nếu gửi cả struct JSON.
- Chỉ cần Q&A: dùng `llm_prompt_block` + câu hỏi (~720 tokens cho 7 doc vs hàng chục nghìn nếu quét full markdown).

**Luồng đề xuất:**

```text
export_llm_context.py → đọc estimated_tokens → nếu OK → DeepSeek Q&A
                      → nếu quá lớn → thu hẹp filter (phòng ban, doc_type)
```

API hiện có: `GET /api/search/qa` (port 8766) — tự cắt excerpt ~3500 chars; export pack phù hợp khi cần **kiểm soát token thủ công** hoặc batch.

---

## Kết luận

| Câu hỏi | Trả lời |
|---------|---------|
| Tìm sâu được chưa? | **Có** — metadata + summary, filter theo tên/loại giấy |
| Trần Đức Hiển | **7 doc**, pack ~720 tokens |
| Bằng cấp BS | **66 doc** trong catalog, pack ~7k tokens (limit 200) |
| Đưa vào LLM | Dùng `export_llm_context.py` → `llm_prompt_block` + `estimated_tokens_prompt` |

Sample files (local): `workspace/ocr_pipeline/07_exports/20260630_2232-*-llm-pack.json`
