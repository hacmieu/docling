# Report — Pilot AI enrich 15 bản ghi (SLA)

## Mục tiêu

Bóc tách metadata bằng AI (`category`, `tags`, `key_fields`, `review_vi`) trên **15 bản ghi**, đo thời gian bắt đầu/kết thúc.

## Thực hiện

```bash
uv run python scripts/ai_enrich_documents.py --limit 15 --sleep-seconds 4 \
  --sla-report workspace/ocr_pipeline/09_logs/20260626_0508-ai-enrich-sla.json
```

Script bổ sung SLA giống OCR batch: per-doc `started_at`/`finished_at`, batch summary JSON.

## Kết quả

| Metric | Giá trị |
|--------|---------|
| Processed | 15 |
| Success (cuối cùng) | **15/15** |
| Skipped (đã enrich trước) | 23 |
| Model | deepseek-v4-pro |

### Lần chạy đầu (8/15)

| Bắt đầu batch | `2026-06-25T22:11:09Z` |
| 8 doc OK | ~9–22s API/doc |
| 1 timeout (id 511) | 120s |
| 6 DNS lỗi | `api.ai-box.vn` không resolve |

### Retry 7 doc failure

| Thời gian | ~2m 50s tổng |
| Kết quả | 7/7 OK, ~12–27s API/doc |

### SLA trung bình (15 doc thành công)

- **API only:** ~16.8s/doc
- **+ sleep 4s:** ~21s/doc wall clock (mạng ổn định)
- **Ước 447 doc:** ~2.6 giờ

## Mẫu output (id 503)

- category: `Hợp đồng lao động`
- tags: 4
- duration: 12.6s

## File SLA

- [20260626_0508-ai-enrich-sla.json](../workspace/ocr_pipeline/09_logs/20260626_0508-ai-enrich-sla.json)
- [20260626_0515-ai-enrich-retry-sla.json](../workspace/ocr_pipeline/09_logs/20260626_0515-ai-enrich-retry-sla.json)

## Bước tiếp

Chạy full batch không `--limit` khi sẵn sàng (~2.5h).
