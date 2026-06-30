# Plan — Hai lượt AI + tối ưu Gemini một lần

## Bối cảnh

Nhiều loại giấy (giấy khai sinh, CCCD, bằng cấp, chứng chỉ hành nghề, hợp đồng…) cần metadata khác nhau. OCR thuần không đủ để lọc compliance.

## Hiện trạng (đã có)

```text
OCR (lượt 1)  →  document_extractions.raw_text
Enrich (lượt 2) → category, doc_type, tags, key_fields
```

Code: `vision_tasks.enrich_vision_extraction`, `ai_enrich.enrich_extraction_from_ocr_text`, `scripts/ai_enrich_documents.py`.

## Ba phương án

### A — Giữ 2 lượt, mở rộng lượt 2 (khuyến nghị ngắn hạn)

1. `metadata_schemas_vi.json` — field theo `doc_type`.
2. Enrich **2 bước trong lượt 2:**
   - 2a: phân loại `doc_type` (prompt hiện tại).
   - 2b: prompt chuyên theo schema (giấy khai sinh → `ho_ten_cha`, `noi_sinh`; CCCD → `so_cccd`, `ngay_cap`; bằng → `chuyen_nganh`).
3. Backfill toàn catalog.

**Ưu:** Tách OCR (ổn định) và extract (đổi schema không đụng vision).  
**Nhược:** 2 API call/doc (vision lane = 3 call nếu tính OCR vision + classify + extract).

### B — Gemini một lần cho ảnh (tối ưu quota)

Đổi `PIPELINE_VISION_OCR_PROMPT` hoặc thêm `PIPELINE_VISION_STRUCTURED_PROMPT`:

```json
{
  "raw_text": "...",
  "doc_type": "can-cuoc-cong-dan",
  "key_fields": { "ten": "...", "so": "...", "ngay_sinh": "..." },
  "tags": ["can-cuoc"],
  "review_vi": "..."
}
```

Parse JSON → ghi `raw_text` + metadata; **bỏ** enrich riêng khi `PIPELINE_VISION_SINGLE_PASS=true`.

**Ưu:** 1 call ảnh = text + meta; giảm 429.  
**Nhược:** Prompt dài; lỗi JSON cần retry; PDF multi-page vẫn cần lane RAW.

### C — Lane RAW (Docling markdown)

Luôn cần **ít nhất 1 lượt AI text** sau markdown — Docling không hiểu ngữ cảnh hành chính. Không gộp được với vision.

## Ma trận loại giấy → lượt AI

| Loại | Lane ưu tiên | Lượt AI tối thiểu |
|------|--------------|-------------------|
| CCCD, giấy khai sinh (ảnh) | Vision | 1 (nếu B) hoặc 2 (OCR + enrich) |
| Bằng cấp, chứng chỉ (scan) | Vision / RAW | 2 |
| Hợp đồng DOCX | RAW | 2 (parse + enrich) |
| PDF nhiều trang | RAW + vision page 1 | 2–3 |

## Việc làm

- [ ] Bổ sung `doc_types` trong `taxonomy_vi.json`: `giay-khai-sinh`, `bang-tot-nghiep`, `chung-chi-hanh-nghe`, …
- [ ] `metadata_schemas_vi.json` + enrich theo schema (phương án A).
- [ ] Pilot `PIPELINE_VISION_SINGLE_PASS` trên 7 doc Trần Đức Hiển (phương án B).
- [ ] `validate_key_fields.py` — báo thiếu field bắt buộc.
- [ ] Backfill + sync Teable.

## Env gợi ý

```bash
PIPELINE_VISION_ENRICH_ENABLED=true
PIPELINE_VISION_ENRICH_PROVIDER=google
PIPELINE_VISION_ENRICH_MODEL=gemini-2.5-flash
# Tương lai:
# PIPELINE_VISION_SINGLE_PASS=true
```
