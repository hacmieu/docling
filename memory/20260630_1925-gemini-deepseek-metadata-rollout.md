# Triển khai Gemini OCR + DeepSeek enrich + schema metadata

**Ngày:** 2026-06-30 19:25

## Đã làm

1. `.env`: `PIPELINE_VISION_ENRICH_PROVIDER=aibox`, `PIPELINE_VISION_ENRICH_MODEL=deepseek-v4-pro`
2. `metadata_schemas_vi.json` + `metadata_schema.py` — field theo doc_type
3. `ai_enrich.py` — enrich 2 bước: classify → extract key_fields theo schema
4. `taxonomy_vi.json` — thêm giấy khai sinh, bằng, chứng chỉ
5. `concepts_vi.json` — concept `chung-chi-con-han`
6. Migration `007_certificate_status_view.sql` — view lọc chứng chỉ + ngày hết hạn
7. `pipeline_config.py` — fix default vision enrich model khi provider=aibox
8. Backfill vision 40 row: log `09_logs/20260630_1920-vision-deepseek-enrich-backfill.log`

## Pilot doc 831

- `doc_type`: can-cuoc-cong-dan
- `enrich_model`: deepseek-v4-pro
- `key_fields`: so_cccd, ngay_sinh, gioi_tinh, ngay_cap, noi_cap, …

## Tiếp

- Teable sync sau backfill
- Re-enrich lane RAW (`ai_enrich_documents --force`) khi cần metadata mới cho PDF/DOCX
