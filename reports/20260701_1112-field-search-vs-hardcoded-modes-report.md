# Báo cáo — Tìm kiếm theo trường SoT vs mode cứng

**Ngày:** 2026-07-01

## Phản hồi user (đúng hướng)

> Chế độ tìm phải là **một trường trên SoT**, autocomplete theo trường đó; các trường khác tương tự.

Đồng ý. Hai pill **Nhân sự / Bằng & chứng chỉ** là shortcut developer, **không** phản ánh mô hình Teable.

## Bản chất mode hiện tại (để thay thế)

```text
"Nhân sự"     ≈  filter DocExtractions.key_fields.ten + rule path Postgres
"degrees"     ≈  filter DocExtractions.ai_doc_type IN (list hardcode)
```

Trên Teable SoT, PCN đã có:

- Cột `phong_ban`, `ai_doc_type`, `ai_category` trên DocExtractions / OwnCloud
- `key_fields_json` chứa `ten`, `so`, `ngay_het_han`, …

**Đúng UX:** chọn trường → gõ → autocomplete từ Teable.

## Kiến trúc đề xuất

```mermaid
flowchart LR
  UI[Search UI]
  FACET[/api/teable/facet/]
  TB[(Teable SoT)]
  CTX[/api/search/context/]
  UI -->|field + q| FACET
  FACET --> TB
  UI -->|filters[]| CTX
  CTX --> TB
```

- **Không** `mode=staff|degrees`
- **Có** `filters: [{ table, field, op, value }]`
- Preset “Hồ sơ nhân sự” (nếu cần) = **bộ filter lưu sẵn**, không logic riêng trong code

## Autocomplete — nguồn dữ liệu

| Trường | Nguồn autocomplete |
|--------|-------------------|
| `phong_ban` | Distinct OwnCloud.phong_ban |
| `ai_doc_type` | Distinct DocExtractions.ai_doc_type (+ taxonomy label VI) |
| `key_fields.ten` | Distinct parse `key_fields_json` → `ten` / `ho_ten` |
| `version_status` | Enum Teable singleSelect |

Postgres **không** feed autocomplete khi SoT = Teable (tránh lệch cache).

## Rule đặc biệt (không phải “mode”)

**Gom hồ sơ cùng folder:** checkbox sau khi đã lọc theo `ten` — mở rộng sang mọi OwnCloud row cùng prefix path. Đây là **post-filter**, không phải chế độ tìm riêng.

## Tác động code hiện tại

| File | Thay đổi |
|------|----------|
| `llm_context_pack.search_context_pack` | `filters[]` thay `mode` |
| `search.html` | Field picker + autocomplete |
| `teable_read.py` | Mở rộng facet + filter query |
| `pg_app.py` | Routes schema/facet |

## Kết luận

User đúng: search phải **field-centric trên Teable**. Mode cũ là nợ kỹ thuật từ giai đoạn Postgres-first; cần refactor theo plan P1–P4.

Chi tiết: [plans/20260701_1112-teable-field-driven-search-plan.md](../plans/20260701_1112-teable-field-driven-search-plan.md)
