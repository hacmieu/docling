# Policy — Teable là Single Source of Truth

**Ngày:** 2026-06-30 23:15

## Quyết định (kiên quyết)

**Teable** là SoT cho metadata catalog mà con người tra cứu, sửa, và lọc.

**Postgres** vẫn là engine xử lý (OCR, enrich, batch) và **read cache** derive từ Teable — **không** là SoT cho metadata đã publish.

## Hiện trạng (cần đổi)

| Thành phần | Hôm nay | Mục tiêu |
|------------|---------|----------|
| Search UI `/search` | Đọc Postgres | Đọc Teable API |
| Catalog webapp | Đọc Postgres | OwnCloud từ Teable; OCR raw có thể Postgres |
| Sync | Postgres → Teable | **Teable → Postgres** (human edits) + Postgres → Teable (pipeline publish) |
| Sửa PCN trên Teable | Không ghi ngược đủ | Webhook / poll → Postgres `human_verified` |

## Bảng Teable SoT

- **OwnCloud** — document header, path, phòng ban, link DocExtractions
- **DocExtractions** — `key_fields_json`, `ai_doc_type`, `ai_tags`, `extracted_summary`

## Liên kết

- Plan: [plans/20260630_2315-teable-sot-migration-plan.md](../plans/20260630_2315-teable-sot-migration-plan.md)
- Report: [reports/20260630_2315-teable-sot-architecture-report.md](../reports/20260630_2315-teable-sot-architecture-report.md)
