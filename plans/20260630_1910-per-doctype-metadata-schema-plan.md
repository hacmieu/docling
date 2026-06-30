# Plan — Schema metadata theo loại giấy tờ

## Mục tiêu

Cho phép lọc SQL/Teable theo trường nghiệp vụ (vd. `ngay_het_han`, `pham_vi`) mà **không** nhập tay 498 file.

## Phương án đề xuất (3 tầng)

### Tầng 1 — Khai báo schema ngoài code (config)

Tạo `workspace/ocr_pipeline/config/metadata_schemas_vi.json`:

```json
{
  "chung-chi-hanh-nghe": {
    "required": ["ten", "so", "ngay", "ngay_het_han", "pham_vi", "don_vi"],
    "optional": ["noi_cap"]
  },
  "can-cuoc-cong-dan": {
    "required": ["ten", "so", "ngay_sinh", "que_quan"],
    "optional": ["ngay_cap", "noi_cap"]
  }
}
```

Đồng bộ `doc_types` trong `taxonomy_vi.json` (thêm `chung-chi-hanh-nghe`, `bang-tot-nghiep`, …).

### Tầng 2 — Enrich động theo doc_type

1. OCR xong → gọi enrich **lần 1** (phân loại `doc_type` — prompt hiện tại).
2. Tra `metadata_schemas_vi.json` theo `doc_type` → build prompt **lần 2** chỉ trích `key_fields` bắt buộc.
3. `apply_enrichment_to_extraction` merge `key_fields` (giữ field cũ nếu lần 2 trống).

Hoặc: một prompt duy nhất nhưng inject danh sách field từ schema vào `ENRICH_PROMPT`.

Bảng `prompt_templates` (Postgres) + Teable PromptTemplates: lưu prompt theo `doc_type_hint` cho chỉnh sửa không cần deploy.

### Tầng 3 — Cột lọc nhanh (tùy chọn)

Khi có field “nóng” dùng filter hàng ngày:

```sql
-- migration 007: generated columns hoặc view
CREATE VIEW document_certificate_status AS
SELECT
  d.id,
  d.phong_ban,
  e.doc_type,
  e.key_fields->>'ten' AS ten,
  (e.key_fields->>'ngay_het_han')::date AS ngay_het_han,
  (e.key_fields->>'ngay_het_han')::date >= CURRENT_DATE AS con_han
FROM documents d
JOIN effective_document_extractions e ON e.document_id = d.id
WHERE e.doc_type LIKE 'chung-chi%';
```

Index GIN trên `key_fields` đã có thể thêm; với date filter nhiều → generated column + btree.

## Backfill

```bash
uv run python scripts/ai_enrich_documents.py --doc-type chung-chi-hanh-nghe
uv run python scripts/backfill_vision_ai_metadata.py --force --sleep-seconds 30
uv run python scripts/sync_extractions_to_teable.py
```

## Validation sau enrich

Script `validate_key_fields.py` (mới): đọc schema config, báo extraction thiếu `required` → queue re-enrich hoặc human review.

## Thứ tự triển khai

1. [ ] Bổ sung `doc_types` + `metadata_schemas_vi.json` (chứng chỉ, CCCD, CCHN, bằng).
2. [ ] Mở rộng `ENRICH_PROMPT` / prompt theo `doc_type_hint`.
3. [ ] Backfill 7 doc Trần Đức Hiển làm pilot.
4. [ ] View `document_certificate_status` + concept `chung-chi-con-han`.
5. [ ] Teable derived field hoặc filter view “Chứng chỉ còn hạn”.

## Không làm

- Không tạo bảng `staff` riêng trước khi cần — nhân sự suy từ path + `key_fields.ten` đủ cho MVP.
- Không thêm cột cứng trên `documents` cho mọi field — giữ JSONB + view.
