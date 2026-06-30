# ASR + Vision sequential rollout

**Thời điểm:** 2026-06-30

## Bước 1 — ASR m4a (doc 991)

- Bật `PIPELINE_INGEST_EXTENSIONS` thêm `.m4a,.mp3`.
- `ingest_converter.py`: ASR converter riêng (`WHISPER_TURBO` + `AsrPipeline`).
- Ingest **OK**: 17423 chars markdown, ~284s (model download lần đầu).
- AI enrich `--force`: category `hành chính`, 3 tags.
- Postgres: **498/498 success**, 0 cataloged.

## Bước 2 — Vision 21 ảnh JPG mới ingest

- Doc IDs: 599,728,747,754–761,776,811,831–837,843.
- Lần 1 (`1105-vision-jpg-batch`): **0/21 OK** — 429 rate limit (song song batch `0820` PDF).
- Đã dừng batch `0820` + `1105` để giải phóng quota.
- Tăng backoff 429 trong `vision_tasks.py` (8 retry, max 120s).
- `PIPELINE_VISION_BATCH_SLEEP_SECONDS=45`.
- Retry: `1115-vision-jpg-batch-retry.log` (chạy nền).

## Artifact

- ASR: `09_logs/20260630_1100-asr-m4a-ingest.json`
- Vision retry: `09_logs/20260630_1115-vision-jpg-batch-retry.log`
