# Playbook — LLM context pack (tìm kiếm sâu + tính tokens)

**Ngày:** 2026-06-30 22:32

## Trạng thái

**Có** metadata để tìm sâu hơn: 474/498 doc có `key_fields`; enrich 2 bước DeepSeek trên vision.

## Công cụ mới

```bash
# Hồ sơ một nhân sự → JSON + ước lượng tokens
uv run python scripts/export_llm_context.py staff "Trần Đức Hiển" \
  -o workspace/ocr_pipeline/07_exports/tran-duc-hien-llm-pack.json

# Bằng/chứng chỉ bác sĩ (toàn catalog)
uv run python scripts/export_llm_context.py degrees --all-catalog --limit 200 \
  -o workspace/ocr_pipeline/07_exports/all-degrees-llm-pack.json
```

Output: `doc_count`, `estimated_tokens_prompt`, `llm_prompt_block` — đưa thẳng vào LLM.

## Ví dụ đã chạy DEV

| Query | Docs | ~Tokens prompt |
|-------|------|----------------|
| Trần Đức Hiển | 7 | 720 |
| Bằng/chứng chỉ (limit 200) | 52+ | ~5–7k |

## Liên kết

- Report: [reports/20260630_2232-deep-search-llm-context-report.md](../reports/20260630_2232-deep-search-llm-context-report.md)
