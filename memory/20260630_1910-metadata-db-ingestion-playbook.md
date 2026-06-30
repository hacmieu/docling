# Playbook — Đưa metadata giấy tờ vào CSDL

**Ngày:** 2026-06-30 19:10

## Câu hỏi

Mỗi loại giấy tờ cần metadata để lọc — dữ liệu đó vào Postgres như thế nào?

## Trả lời ngắn

**Không nhập tay từng file.** Pipeline tự sinh metadata sau OCR:

```text
OwnCloud file → documents (path, markdown)
            → document_extractions.raw_text (lane OCR)
            → AI enrich (category, doc_type, tags, key_fields)
            → effective_document_extractions (waterfall)
            → Teable DocExtractions (sync)
```

Metadata “lọc được” nằm ở cột **có cấu trúc** (`doc_type`, `tags`, `category`) + **JSONB linh hoạt** (`key_fields`).

## Ba lớp metadata

| Lớp | Nơi lưu | Ai ghi | Dùng để |
|-----|---------|--------|---------|
| Định danh file | `documents.owncloud_path`, `phong_ban` | ingest | Lọc theo phòng / thư mục nhân sự |
| Phân loại | `document_extractions.category`, `doc_type`, `tags` | AI enrich + `taxonomy_vi.json` | Filter Teable/SQL theo loại giấy |
| Trường nghiệp vụ | `document_extractions.key_fields` (JSONB) | AI enrich (+ human verify sau) | Tên, số, ngày, hạn, phạm vi… |

## Schema key_fields hiện tại

`ENRICH_PROMPT` (`ai_enrich.py`) yêu cầu:

```json
{"ten": "...", "so": "...", "ngay": "...", "don_vi": "..."}
```

Thiếu cho compliance: `ngay_het_han`, `pham_vi`, `so_cccd` — cần mở rộng theo `doc_type`.

## Điểm ghi CSDL (code)

- Sau ingest markdown: `upsert_local_llm_ocr_from_markdown` → row `local_llm_ocr`
- Sau enrich RAW: `upsert_deepseek_extraction` hoặc `apply_enrichment_to_extraction`
- Vision lane: `persist_vision_extraction` → `enrich_vision_extraction` → cùng `apply_enrichment_to_extraction`

Bảng SoT: `document_extractions`. View tra cứu: `effective_document_extractions`.

## Human override

`source_type = human_verified` có `priority_score` cao nhất — sửa metadata trên Teable/webchat rồi ghi ngược Postgres (flow đã thiết kế trong migration 002).

## Liên kết

- Plan: [plans/20260630_1910-per-doctype-metadata-schema-plan.md](../plans/20260630_1910-per-doctype-metadata-schema-plan.md)
- Báo cáo: [reports/20260630_1910-metadata-to-database-guide.md](../reports/20260630_1910-metadata-to-database-guide.md)
