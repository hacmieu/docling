# Báo cáo triển khai — DeepSeek enrich + metadata schema

**Ngày:** 2026-06-30

## Tóm tắt

Đã triển khai chiến lược **Gemini Flash OCR → DeepSeek v4 Pro metadata** với enrich **2 bước** theo schema từng loại giấy.

## Thay đổi code

| File | Nội dung |
|------|----------|
| `metadata_schemas_vi.json` | Field bắt buộc/tuỳ chọn per doc_type |
| `metadata_schema.py` | Loader + lookup schema |
| `ai_enrich.py` | Classify → extract; merge key_fields |
| `taxonomy_vi.json` | +6 doc_types (CCCD, giấy khai sinh, bằng, chứng chỉ…) |
| `pipeline_config.py` | Vision enrich model mặc định = deepseek khi aibox |
| `007_certificate_status_view.sql` | View filter chứng chỉ + parse ngay_het_han |

## Cấu hình runtime

```bash
PIPELINE_VISION_ENRICH_PROVIDER=aibox
PIPELINE_VISION_ENRICH_MODEL=deepseek-v4-pro
```

## Kết quả pilot (doc 831 — CCCD)

```json
{
  "doc_type": "can-cuoc-cong-dan",
  "key_fields": {
    "so_cccd": "092000693101",
    "ten": "Phạm Công Nguyên",
    "ngay_sinh": "28/08/1992",
    "gioi_tinh": "Nam",
    "ngay_cap": "13/04/2021",
    "noi_cap": "Cục Cảnh sát quản lý hành chính về trật tự xã hội"
  }
}
```

`enrich_model` = `deepseek-v4-pro`, `model_name` vision = Gemini.

## Filter sau triển khai

```sql
SELECT * FROM document_certificate_status
WHERE owncloud_path ILIKE '%2.CĐHA%'
  AND (ngay_het_han IS NULL OR ngay_het_han >= CURRENT_DATE);
```

## Backfill

40 extraction `google_vision` đang re-enrich (2 call/doc × ~20s). Log: `09_logs/20260630_1920-vision-deepseek-enrich-backfill.log`.

Lane RAW (498 `deepseek_cleanup`) chưa re-enrich hàng loạt — chạy `ai_enrich_documents --force` khi sẵn sàng (~2h).
