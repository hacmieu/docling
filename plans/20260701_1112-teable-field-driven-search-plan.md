# Plan — Search UI driven by Teable fields + autocomplete

## Nguyên tắc

1. **SoT = Teable** — facet và filter đọc/ghi semantics từ cột Teable.
2. **Không hardcode** `staff` / `degrees` / `DEGREE_DOC_TYPES` trong UI.
3. **Autocomplete** mỗi trường = gợi ý từ giá trị distinct trên Teable (có prefix `q`).
4. Postgres chỉ cache mirror; không là nguồn facet khi production.

## UI mục tiêu (thay 2 pill mode)

```text
[Bảng ▼ OwnCloud | DocExtractions]
[Trường ▼ phong_ban | ai_doc_type | key_fields.ten | …]
[Giá trị 🔍 autocomplete________________]
[+ Thêm điều kiện]
[Tìm kiếm]
```

Ví dụ nghiệp vụ (cùng engine, không mode riêng):

| PCN muốn | Bảng | Trường | Giá trị |
|----------|------|--------|---------|
| Hồ sơ Trần Đức Hiển | DocExtractions | `key_fields.ten` | Trần Đức Hiển |
| Bằng BS toàn viện | DocExtractions | `ai_doc_type` | bang-tot-nghiep |
| CCHN hết hạn | DocExtractions | `key_fields.ngay_het_han` | &lt; today (sau) |
| Theo phòng CĐHA | OwnCloud | `phong_ban` | CĐHA |

## API mới

```http
GET /api/teable/schema
  → tables, fields (type, facetable, label VI)

GET /api/teable/facet?table=extractions&field=ai_doc_type&q=chung&limit=20
  → ["chung-chi-hanh-nghe", "chung-chi-dao-tao", ...]

POST /api/search/context
  body: {
    "filters": [
      {"table": "extractions", "field": "key_fields.ten", "op": "contains", "value": "Trần Đức Hiển"},
      {"table": "owncloud", "field": "phong_ban", "op": "eq", "value": "CĐHA"}
    ],
    "limit": 100
  }
```

## Module code

| File | Việc |
|------|------|
| `teable_facet.py` | List fields, distinct values, Teable filter DSL |
| `teable_search.py` | Join OwnCloud ↔ DocExtractions theo `doc_id` / link |
| `search_context_pack.py` | Nhận `filters[]` thay vì `mode=staff|degrees` |
| `search.html` | Dynamic filter rows + autocomplete dropdown |

## Map mode cũ → filter (migration tạm)

| Mode cũ | Filter tương đương |
|---------|-------------------|
| staff + tên | `key_fields.ten` contains + (optional) expand OwnCloud cùng `doc_id` set |
| degrees | `ai_doc_type` in taxonomy group **hoặc** user chọn từng `ai_doc_type` autocomplete |

**Folder sibling expansion** (7 doc cùng thư mục): không phải “mode” — là rule **sau filter** khi trường là `key_fields.ten` và bật “Gom hồ sơ cùng folder OwnCloud”.

## Teable implementation notes

- Distinct: paginate `GET /table/{id}/record` + aggregate in-memory (MVP) hoặc Teable view/filter nếu có.
- `key_fields_json`: parse JSON server-side; facet `key_fields.{key}` theo `metadata_schemas_vi.json`.
- Chỉ `version_status=active` mặc định.

## Phase

### P1 — Schema + facet API

- [ ] `GET /api/teable/schema` từ field metadata Teable + config virtual key_fields.*
- [ ] `GET /api/teable/facet` MVP (scan + cache 15 phút)

### P2 — Search context từ filters

- [ ] `POST /api/search/context` filter-driven, đọc Teable
- [ ] Deprecate `mode=staff|degrees` query params

### P3 — UI

- [ ] Thay mode pills bằng field picker + autocomplete
- [ ] Saved filter presets (optional): “Hồ sơ nhân sự”, “Bằng BS” = **bookmark filter**, không hardcode logic

### P4 — Dọn code

- [ ] Xóa `DEGREE_DOC_TYPES`, `search_staff_documents` path hacks → Teable join hoặc rule “expand folder” tách biệt

## Env

```bash
CATALOG_SOT=teable
TEABLE_FACET_CACHE_TTL=900
```
