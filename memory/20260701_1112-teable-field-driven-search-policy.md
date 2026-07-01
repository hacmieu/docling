# Policy — Tìm kiếm theo trường Teable (không hardcode mode)

**Ngày:** 2026-07-01 11:12

## Quyết định

**Bỏ** chế độ cứng `staff` / `degrees` trên UI.

**Thay bằng:** mọi bộ lọc = **một trường trên SoT (Teable)** + autocomplete giá trị từ Teable.

## Vì sao mode cũ không ổn

| Mode cũ | Thực chất | Vấn đề |
|---------|-----------|--------|
| Nhân sự | Lọc `key_fields.ten` + mở rộng path Postgres | Logic ẩn trong code, không map 1-1 cột Teable |
| Bằng & chứng chỉ | List `DEGREE_DOC_TYPES` hardcode | Taxonomy đổi → sửa code; không phải field Teable |

PCN nghĩ theo **cột bảng** (phòng ban, loại giấy, tên, số CCHN…), không nghĩ theo “mode developer”.

## Mô hình mục tiêu

```text
Chọn bảng SoT (OwnCloud | DocExtractions)
  → Chọn trường (phong_ban | ai_doc_type | ten trong key_fields | …)
  → Autocomplete giá trị từ Teable
  → (Tuỳ chọn) thêm filter AND trường khác
  → Kết quả + LLM context
```

## Trường SoT ưu tiên (facet)

**OwnCloud:** `phong_ban`, `file_name`, `catalog_status`, `Status`, `active_source`

**DocExtractions:** `ai_doc_type`, `ai_category`, `version_status`, `source_type`

**key_fields (JSON):** `ten`, `ho_ten`, `so`, `chuyen_nganh`, `ngay_het_han` — expose như virtual field `key_fields.ten`

## Autocomplete

- Nguồn: **Teable API** (distinct / search prefix trên cột)
- Không autocomplete từ Postgres khi `CATALOG_SOT=teable`
- Cache facet values (TTL ngắn) được phép nếu derive từ Teable

## Liên kết

- Plan: [plans/20260701_1112-teable-field-driven-search-plan.md](../plans/20260701_1112-teable-field-driven-search-plan.md)
- Report: [reports/20260701_1112-field-search-vs-hardcoded-modes-report.md](../reports/20260701_1112-field-search-vs-hardcoded-modes-report.md)
