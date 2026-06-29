# Memory — Flow đa phiên bản & priority extraction

## Flow thực tế (nhân viên BV)

```
Upload OCIS
    → OCR local (priority 30) ─────────────────┐
    → Google Vision đọc ảnh (priority 70) ─────┤
    → DeepSeek làm sạch/enrich (priority 50) ──┤→ document_extractions (nhiều version)
    → User Webchat + prompt gợi ý (95) ──────┤
    → User xác nhận trên Teable (100) ────────┘
         ↓
    active = MAX(priority) per document
         ↓
    Teable UI (OwnCloud + DocExtractions + PromptTemplates)
```

## Priority (cao → thấp)

| source_type | Điểm | Ai tạo |
|-------------|------|--------|
| human_verified | 100 | Nhân viên lưu/xác nhận Teable |
| human_webchat | 95 | Webchat AI + user chỉnh |
| google_vision | 70 | API Google đọc ảnh |
| deepseek_cleanup | 50 | DeepSeek sau OCR local |
| local_llm_ocr | 30 | EasyOCR pipeline |

## Postgres: **6 bảng**

`documents`, `tags`, `categories`, `document_tags`, **`prompt_templates`**, **`document_extractions`**

Backfill: 470 `local_llm_ocr` + 38 `deepseek_cleanup`.

## Teable (base Quản lý Nội bộ)

| Bảng | ID |
|------|-----|
| OwnCloud | tblNwc8A1llcPa0JcsA (+ active_priority, active_source) |
| PromptTemplates | tbluFFwWvqfWYyngD7r |
| DocExtractions | tblnLAXYbsxFtuFhbJa (link → OwnCloud) |

## Scripts

- `setup_teable_extraction_schema.py` — tạo bảng/field/link
- `migrate_document_extractions.py` — Postgres migration + backfill
