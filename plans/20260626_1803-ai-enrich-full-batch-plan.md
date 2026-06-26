# Plan — Full batch AI enrich sau pilot 15

## Pilot đã xác nhận

- SLA script ổn; ~17s API + 4s sleep/doc.
- Lỗi mạng: retry `--doc-id ID --force` hoặc chạy lại (failure không bị skip).

## Full batch

```bash
uv run python scripts/ai_enrich_documents.py \
  --sleep-seconds 4 \
  --sla-report workspace/ocr_pipeline/09_logs/YYYYMMDD_HHMM-ai-enrich-full-sla.json
```

- Không `--limit` → xử lý mọi doc `status IN (success, cataloged)` chưa `ai_review_status=success`.
- Ước ~439 doc còn lại × ~21s ≈ **2.5–3 giờ**.

## Retry failure

```bash
docker exec ocr-pipeline-postgres psql -U ocr -d ocr_catalog -c \
  "SELECT id FROM documents WHERE ai_review_status='failure';"

for id in ...; do
  uv run python scripts/ai_enrich_documents.py --doc-id $id --force --sleep-seconds 4
done
```

## Sau enrich

1. Kiểm tra phân bố `ai_category` — chuẩn hóa taxonomy.
2. Bật concept search FTS + tag.
3. Mirror subset sang Teable khi có token.
