# Memory — Chuẩn hóa metadata + migrate DocExtractions

## Chuẩn hóa

- `ai_category` → **nhãn tiếng Việt chuẩn** (VD: `Nhân sự`, không `nhân sự`/`Nhân sự` lẫn lộn)
- `ai_doc_type` → **slug kebab-case** (VD: `quyet-dinh`, `hop-dong-lao-dong`)
- `ai_tags` → **slug** (VD: `nhan-su`, `hop-dong`) — Teable `multipleSelect`

Taxonomy: `workspace/ocr_pipeline/config/taxonomy_vi.json`

## Teable field types

| Field | Type |
|-------|------|
| ai_category | singleSelect |
| ai_doc_type | singleSelect |
| ai_tags | multipleSelect |

Áp dụng trên **OwnCloud** và **DocExtractions**.

## DocExtractions migrate

- **462** phiên bản HTH-Shared (470 RAW + 38 DeepSeek overlap per doc → 2 rows/doc typical)
- RAW: `version_label` RAW-vN, chỉ `raw_text_preview`
- DeepSeek: `DeepSeek-vN`, `ai_category`, `ai_doc_type`, `ai_tags`, `key_fields_json`

## Scripts

```bash
uv run python scripts/normalize_catalog_metadata.py
uv run python scripts/upgrade_teable_metadata_fields.py
uv run python scripts/sync_catalog_to_teable.py
uv run python scripts/sync_extractions_to_teable.py
```
