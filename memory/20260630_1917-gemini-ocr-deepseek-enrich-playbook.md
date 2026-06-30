# Playbook — Gemini OCR + DeepSeek Pro enrich

**Ngày:** 2026-06-30 19:17

## Quyết định

- **Lượt 1:** Gemini Flash — chỉ OCR (ảnh/PDF trang 1), tận dụng free tier vision.
- **Lượt 2:** DeepSeek v4 Pro — enrich metadata cho **mọi** lane (RAW markdown lẫn text từ Gemini).

DSv4 Pro ổn cho phân loại tiếng Việt + trích `key_fields`; không cần Gemini enrich (tránh 429 kép).

## Env khuyến nghị

```bash
PIPELINE_RAW_ENRICH_MODEL=deepseek-v4-pro
PIPELINE_VISION_ENRICH_PROVIDER=aibox
PIPELINE_VISION_ENRICH_MODEL=deepseek-v4-pro
PIPELINE_VISION_ENRICH_ENABLED=true
```

## Ghi DB

| Cột | Vision lane |
|-----|-------------|
| `model_name` | `gemini-2.5-flash` (OCR) |
| `enrich_model` | `deepseek-v4-pro` (metadata) |

## Mục tiêu filter

Metadata (`doc_type`, `tags`, `key_fields`) thu hẹp không gian tìm kiếm trước khi quét `markdown` hoặc gọi Q&A.

## Liên kết

- Plan: [plans/20260630_1917-gemini-ocr-deepseek-enrich-plan.md](../plans/20260630_1917-gemini-ocr-deepseek-enrich-plan.md)
- Report: [reports/20260630_1917-metadata-shrink-search-space-report.md](../reports/20260630_1917-metadata-shrink-search-space-report.md)
