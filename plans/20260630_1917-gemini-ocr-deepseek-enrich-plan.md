# Plan — Gemini Flash OCR + DeepSeek Pro metadata (mọi lane)

## Nguyên tắc

1. **Tách vai trò:** Gemini = đọc chữ từ ảnh; DeepSeek = hiểu ngữ cảnh + JSON metadata.
2. **Một model enrich:** `deepseek-v4-pro` cho lane RAW và lane Vision — đồng nhất chất lượng, dễ backfill.
3. **Metadata là điều kiện filter:** không gọi Q&A / full-text trên 498 doc nếu đã lọc được bằng `doc_type` + `key_fields`.

## Cấu hình

```bash
# Lane 1 RAW
PIPELINE_RAW_ENRICH_MODEL=deepseek-v4-pro

# Lane 2 Vision OCR
PIPELINE_VISION_PROVIDER=google
PIPELINE_VISION_MODEL=gemini-2.5-flash

# Lane 2 enrich — BẮT BUỘC set aibox (mặc định code = google nếu vision=google)
PIPELINE_VISION_ENRICH_PROVIDER=aibox
PIPELINE_VISION_ENRICH_MODEL=deepseek-v4-pro
PIPELINE_VISION_ENRICH_ENABLED=true
PIPELINE_VISION_ENRICH_FALLBACK_INHERIT=false
```

Code: `enrich_api_config(lane="vision")` → `call_aibox_enrich` khi provider ≠ google.

## Thu hẹp không gian tìm kiếm

```text
Trước metadata:  WHERE markdown ILIKE '%chứng chỉ%'     → ~hàng trăm doc
Sau metadata:    WHERE doc_type LIKE 'chung-chi%'
                   AND key_fields->>'ngay_het_han' >= today
                   AND phong_ban = '2.CĐHA'              → vài chục doc
Q&A AI:          chỉ trên subset đã lọc (limit 10–20)
```

Bổ sung `concept_search` / SQL filter theo `key_fields` khi schema mở rộng.

## Bước triển khai

1. [x] Tách `model_name` vs `enrich_model` trong DB (migration 006).
2. [ ] Đổi `.env` production: `PIPELINE_VISION_ENRICH_PROVIDER=aibox`.
3. [ ] Mở rộng `ENRICH_PROMPT` + `metadata_schemas_vi.json` theo loại giấy.
4. [ ] Backfill vision rows: `backfill_vision_ai_metadata.py --force` (DeepSeek, không 429 Gemini enrich).
5. [ ] Sync Teable; view filter theo `ai_doc_type` + `key_fields_json`.
6. [ ] Thêm index / view cho field nóng (`ngay_het_han`, `ten`).

## Backfill lệnh

```bash
# Đảm bảo .env có VISION_ENRICH_PROVIDER=aibox
uv run python scripts/backfill_vision_ai_metadata.py --force
uv run python scripts/ai_enrich_documents.py --force   # RAW lane nếu cần
uv run python scripts/sync_extractions_to_teable.py
```

## Không làm

- Không dùng Gemini cho enrich khi đã chọn DSv4 Pro (trừ pilot so sánh chất lượng).
- Không search full catalog bằng AI khi SQL filter đủ.
