# Báo cáo: Teable cập nhật ngay sau mỗi Vision OCR

**Thời điểm:** 2026-06-30 08:51

## Tóm tắt

Đã triển khai **incremental Teable sync** — mỗi doc Vision OCR xong được đẩy lên Teable ngay (DocExtractions + OwnCloud effective fields), không cần đợi batch hay loop 5 phút.

## Luồng mới

```text
vision_ocr_document(doc)
  → INSERT document_extractions (google_vision)
  → sync_extraction_and_document()
       ├─ POST/PATCH Teable DocExtractions (Vision-vN, raw_text_preview)
       ├─ recompute effective_* trên Postgres
       └─ PATCH Teable OwnCloud (active_source=google_vision, active_priority=70, version_count)
```

## Backfill

| Hạng mục | Kết quả |
|----------|---------|
| Doc vision trước đó | 18 |
| Backfill Teable | **18/18 OK** |
| OwnCloud patched | 18/18 |

## Batch đang chạy

```bash
run_vision_batch_sync.py --sync-teable --sleep-seconds 12
# log: workspace/ocr_pipeline/09_logs/20260630_0820-vision-batch-teable.log
```

Log mẫu khi thành công:

```
[OK] doc_id=… extraction_id=… text_len=…
[TEABLE-OK] doc_id=… extraction_created owncloud_patched=True
```

## Lưu ý quota Google

Nếu gặp `429` / `rate limited`, tăng `--sleep-seconds` lên **15–20** khi restart batch.

## Tắt sync (nếu cần debug)

```bash
uv run python scripts/run_vision_batch_sync.py --no-sync-teable ...
```
