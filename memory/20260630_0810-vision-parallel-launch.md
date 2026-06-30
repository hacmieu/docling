# Memory: Khởi động Google Vision batch song song

**Thời điểm:** 2026-06-30 08:10

## Hành động

- `check_vision_api.py` → `image_probe_status=200`, model `gemini-2.5-flash`
- Khởi chạy nền `run_vision_batch_sync.py` — **444 doc**, `--sleep-seconds 12`, `--skip-existing`
- Pilot 3 doc (503–505) được bỏ qua
- Chạy song song với Teable sync loop (PID từ 29/06, 5 phút/vòng)

## Pilot đầu batch

| doc_id | extraction_id | text_len | Kết quả |
|--------|---------------|----------|---------|
| 506 | 1338 | 1268 | OK |
| 507 | 1339 | 1097 | OK |

## Log

- `workspace/ocr_pipeline/09_logs/20260630_0810-vision-batch.log`
- JSON SLA khi xong: `20260630_0810-vision-batch.json`

## Lý do 444 thay vì 467

Query batch yêu cầu `local_path` hợp lệ + `owncloud_path LIKE project/hth-shared-drive%` + chưa có `google_vision`. ~23 doc không đủ điều kiện file local.
