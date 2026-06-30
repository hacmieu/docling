# Plan — Tìm bác sĩ & chứng chỉ còn hạn

## Use case A — Mọi tài liệu của một bác sĩ

**Ví dụ:** Trần Đức Hiển

| Bước | Công cụ | Cách làm |
|------|---------|----------|
| 1 | Teable OwnCloud | Filter `phong_ban` hoặc `owncloud_path` chứa tên; mở link **DocExtractions** |
| 2 | API | `GET /api/search?q=Trần Đức Hiển&phong_ban=2.CĐHA&limit=50` |
| 3 | Postgres | `key_fields->>'ten' ILIKE '%Hiển%'` hoặc path ILIKE `%TRẦN ĐỨC HIỂN%` |

## Use case B — Bác sĩ có chứng chỉ còn hạn theo phòng khám

**Luồng đề xuất (sau khi bổ sung schema):**

1. Lọc phòng: `phong_ban = '2.CĐHA'` (hoặc tên phòng khám).
2. Lọc loại: `doc_type IN ('chung-chi', 'chung-chi-hanh-nghe', ...)` hoặc concept `pham-vi-hanh-nghe`.
3. Lọc hạn: `key_fields->>'ngay_het_han' >= CURRENT_DATE` (cần enrich bổ sung field).
4. So khớp quy định mới: concept registry + Q&A `GET /api/search/qa?q=...`.

## Việc cần làm tiếp

- [ ] Mở rộng `ENRICH_PROMPT` thêm `ngay_het_han`, `pham_vi` trong `key_fields`.
- [ ] Thêm concept `chung-chi-con-han` vào `concepts_vi.json`.
- [ ] Teable View: filter `doc_type` + cột `key_fields_json` (hoặc field derived `het_han`).
