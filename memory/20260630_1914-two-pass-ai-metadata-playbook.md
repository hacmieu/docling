# Playbook — Hai lượt AI: OCR và trích metadata

**Ngày:** 2026-06-30 19:14

## Kết luận ngắn

**Đúng** — giấy khai sinh, CCCD, bằng cấp, chứng chỉ… cần AI đọc **ngữ cảnh** để lấy metadata có cấu trúc (`ten`, `so`, `ngay_sinh`, `ngay_het_han`…), không chỉ chữ OCR thô.

**Đã có sẵn lượt 2** trong code: `enrich_extraction_from_ocr_text` sau mỗi lane OCR.

**Gemini hiện chưa “lấy luôn” một lần** — `call_vision_ocr` chỉ prompt plain text; enrich là API call riêng (có thể cùng model `gemini-2.5-flash`).

## Hai lane hiện tại

| Lane | Lượt 1 (OCR) | Lượt 2 (metadata) |
|------|--------------|-------------------|
| RAW (PDF/DOCX/…) | Docling/EasyOCR → markdown | DeepSeek (`deepseek_cleanup`) |
| Vision (JPG/PDF ảnh) | Gemini vision → plain text | Gemini hoặc DeepSeek (`PIPELINE_VISION_ENRICH_*`) |

## Gap

- `key_fields` schema chung 4 field — chưa đủ cho từng loại giấy.
- Chưa có enrich theo `doc_type` (giấy khai sinh vs CCCD vs bằng cấp).
- Tối ưu Gemini: **một prompt JSON** (text + metadata) — chưa triển khai.

## Liên kết

- Plan: [plans/20260630_1914-two-pass-ai-metadata-extraction-plan.md](../plans/20260630_1914-two-pass-ai-metadata-extraction-plan.md)
- Report: [reports/20260630_1914-two-pass-ai-metadata-report.md](../reports/20260630_1914-two-pass-ai-metadata-report.md)
