# Plan: Sync Teable ngay sau mỗi Google Vision OCR

**Thời điểm:** 2026-06-30 08:51

## Vấn đề

Vision OCR chậm (~25–30s/doc); user muốn thấy kết quả trên Teable ngay, không đợi batch xong hay loop 5 phút.

## Giải pháp

1. Module `workspace/ocr_pipeline/teable_incremental_sync.py`:
   - `TeableSyncContext` — cache map Teable một lần đầu batch
   - `sync_extraction_and_document()` — sau mỗi OCR: upsert DocExtractions + recompute effective + PATCH OwnCloud

2. `run_vision_batch_sync.py` — `--sync-teable` mặc định **ON** (`--no-sync-teable` để tắt)

3. `sync_extractions_to_teable.py` — thêm `google_vision` vào default source types

4. `scripts/backfill_vision_teable_sync.py` — đẩy các doc vision đã OCR trước khi có tính năng này

## Triển khai

- Backfill **18/18** doc vision lên Teable OK
- Restart batch với sync incremental; log `20260630_0820-vision-batch-teable.log`
- 429 quota: tăng `--sleep-seconds` lên 15–20 nếu fail hàng loạt
