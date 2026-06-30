# Plan — Deep search + LLM token budgeting

## Mục tiêu

Trả kết quả **đã lọc + định lượng tokens** trước khi gọi LLM.

## Luồng

```text
SQL metadata filter → llm_context_pack → estimated_tokens → LLM
```

Không quét full markdown 498 doc.

## Đã triển khai

- [x] `llm_context_pack.py` — staff search + doc_type search + token estimate
- [x] `scripts/export_llm_context.py` — CLI staff / degrees
- [ ] API endpoint `/api/search/context` (tuỳ chọn)
- [ ] RAW lane re-enrich schema mới cho PDF-only docs

## Query patterns

| Use case | Filter |
|----------|--------|
| Nhân sự | `key_fields.ten` + folder prefix + Hiển/Hiền |
| Bằng BS | `doc_type IN (bang-tot-nghiep, chung-chi-*)` |
| Còn hạn | `document_certificate_status` view |
