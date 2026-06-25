# Plan — AI taxonomy (category / tag) + context API

## Mục tiêu

Gán **category**, **tag**, **doc_type**, **key_fields** cho catalog Postgres đã OCR; xây **context API** kiểu email (lọc trước → AI sau).

## Phân tầng metadata (khuyến nghị)

```
┌─────────────────────────────────────────────────────────┐
│ L1 — Deterministic (không AI)                           │
│   owncloud_path → dept / drive                          │
│   mtime, status, sha256, file extension                 │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ L2 — Rule-based tags                                    │
│   Ví dụ: path chứa "PhongKham" → tag "phong-kham"       │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ L3 — AI enrich (1 lần / doc, re-run khi hash đổi)      │
│   category (1), tags (n), doc_type, key_fields, review  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ L4 — Human verified (optional)                          │
│   import_verified_metadata.py → verified_metadata       │
└─────────────────────────────────────────────────────────┘
```

## Định nghĩa field

| Field | Cardinality | Ví dụ | Ghi chú |
|-------|-------------|-------|---------|
| `category` | 1 | Hợp đồng, Quyết định, Biên bản | Menu chính UI |
| `tags` | n | bảo hiểm, đấu thầu, nội bộ | Facet filter + FTS bổ sung |
| `doc_type` | 1 | hop-dong, quyet-dinh | Machine-friendly slug |
| `ai_key_fields` | object | ten, so, ngay, don_vi | Thay thế một phần OCR grep |
| `label` | ≈ tag | — | Dùng chung bảng `tags`, không tách thêm |

## Context API (tương tự email API cũ)

Endpoint logic (chưa code — phase P2):

```
GET /api/documents/context?
  dept=...&
  date_from=...&date_to=...&
  category=...&
  tag=...&
  q=...&          # FTS markdown
  limit=20
```

Response: `{ items: [{ id, path, category, tags, key_fields, excerpt_markdown }] }`  
→ User/ agent gọi LLM chỉ với payload này, không quét full catalog.

## Rollout

### P1 — Enrich batch (now)

```bash
uv run python scripts/ai_enrich_documents.py --sleep-seconds 6
# pilot: --limit 20 trước, rồi full
```

- Kiểm tra `ai_review_status`, log lỗi JSON parse.
- Sau batch: `SELECT ai_category, count(*) GROUP BY 1` — gom category lệch chuẩn.

### P2 — Taxonomy hygiene

- File `workspace/ocr_pipeline/config/taxonomy_vi.json`: allowed categories + tag normalize map.
- Post-process trong enrich hoặc script `normalize_ai_tags.py`.
- Link `ai_category` → bảng `categories` (hiện chỉ lưu cột text + tags qua `link_document_tags`).

### P3 — Context API

- FastAPI route trong `pg_app.py` hoặc `scripts/context_api.py`.
- Postgres: `to_tsvector('simple', markdown)` hoặc `pg_trgm` nếu cần tiếng Việt.
- Mirror subset sang Teable khi có token.

### P4 — Q&A

- Chỉ khi user hỏi: gọi context API → DeepSeek trả lời trên ≤20 doc.

## Tránh

- Gọi LLM mỗi lần search chỉ để gán tag.
- Vector DB toàn bộ 447 doc ngay từ đầu.
- Category quá chi tiết (trùng vai trò tag).

## Done criteria

- [ ] ≥90% doc `success` có `ai_category` + ≥2 `ai_tags`
- [ ] Context API trả đúng filter path + date + tag
- [ ] Webapp/Teable filter theo category/tag
