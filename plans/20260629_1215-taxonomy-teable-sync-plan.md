# Plan — Taxonomy & Teable typed fields

## Quy ước chuẩn hóa (bắt buộc trước sync)

| Field | Postgres | Teable |
|-------|----------|--------|
| ai_category | Label VN từ taxonomy | singleSelect (label) |
| ai_doc_type | slug `kebab-case` | singleSelect (slug) |
| ai_tags | JSON array slug | multipleSelect |

## RAW vs DeepSeek trên DocExtractions

| source_type | Fields điền |
|-------------|-------------|
| local_llm_ocr | raw_text_preview, model_name |
| deepseek_cleanup | + ai_category, ai_doc_type, ai_tags, key_fields_json, extracted_summary |

## P1

- [ ] Webchat lưu `human_webchat` → normalize trước POST Teable
- [ ] Google Vision → `google_vision` row
- [ ] Auto `upgrade_teable_metadata_fields` khi tag mới xuất hiện

## P2

- Lookup trên OwnCloud: active extraction từ MAX(priority)
