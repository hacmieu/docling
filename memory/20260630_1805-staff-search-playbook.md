# Playbook tìm kiếm nhân sự / bác sĩ

**Thời điểm:** 2026-06-30

## Ví dụ thực: Trần Đức Hiển

Thư mục OCIS: `.../2.CĐHA/BÁC SĨ/TRẦN ĐỨC HIỂN/...` — **7 documents** (831–837): CCCD, bằng cấp, chứng chỉ đào tạo, CCHN.

Metadata effective (`key_fields.ten`) đã có tên; một số OCR ghi **Hiền** vs **Hiển** (cần search mờ).

## 3 lớp tìm kiếm (ưu tiên)

1. **Cấu trúc path** (`phong_ban` + tên thư mục nhân sự) — nhanh, không token AI.
2. **Postgres / API** — `markdown`, `key_fields`, tags qua `effective_document_extractions`.
3. **Teable** — filter View OwnCloud + drill-down DocExtractions (ERD).

## Chứng chỉ còn hạn

Hiện `key_fields` có `ngay` (thường ngày cấp/sinh), **chưa có `ngay_het_han` chuẩn** trên mọi doc → cần mở rộng enrich prompt + concept `chung-chi-con-han` trước khi query hết hạn tự động.
