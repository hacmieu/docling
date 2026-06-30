# Memory: Incremental Teable sync sau Vision OCR

**Thời điểm:** 2026-06-30 08:51

## Thay đổi code

- `teable_incremental_sync.py` — sync từng extraction + PATCH OwnCloud (`active_source`, `active_priority`, `extraction_version_count`)
- `run_vision_batch_sync.py` — `--sync-teable` default ON, log `[TEABLE-OK]` / `[TEABLE-FAIL]`
- `sync_extractions_to_teable.py` — include `google_vision`, label `Vision-v{n}`
- `backfill_vision_teable_sync.py` — backfill 18 doc đã OCR trước đó

## Kết quả backfill

18/18 OK, `owncloud_patched=True` cho mỗi doc (503–530 pilot range).

## Batch mới

- Dừng batch cũ (không sync Teable)
- Khởi động lại 429 doc còn lại với `Teable incremental sync: ON`
- Log: `workspace/ocr_pipeline/09_logs/20260630_0820-vision-batch-teable.log`
