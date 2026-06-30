# Báo cáo ASR + Vision tuần tự

**Ngày:** 2026-06-30

## Bước 1 — ASR (hoàn tất)

| Item | Kết quả |
|------|---------|
| Doc 991 `.m4a` | **OK** — 17 423 ký tự transcript |
| Thời gian | ~284s (tải Whisper model lần đầu) |
| AI enrich | category `hành chính`, 3 tags |
| Catalog | **498/498 success** |

## Bước 2 — Vision 21 JPG (bị chặn quota)

- Google API free tier `gemini-2.5-flash`: **20 RPM** — hai batch song song (PDF + JPG) gây 429 hàng loạt.
- Đã dừng batch PDF `0820`; tăng backoff + parse `retry in Ns` từ response.
- Pilot doc 599: vẫn 429 sau ~12 phút retry → cần chờ quota reset và chạy **tuần tự** sleep ≥60s/doc.

### Lệnh resume (khi quota ổn)

```bash
uv run python scripts/run_vision_batch_sync.py \
  --doc-id 599 --doc-id 728 ... \
  --sleep-seconds 60 --skip-existing \
  --log-file workspace/ocr_pipeline/09_logs/YYYYMMDD-vision-jpg-resume.log
```

## Code thay đổi

- `ingest_converter.py`: ASR pipeline (`WHISPER_TURBO`)
- `vision_tasks.py`: backoff 429 thông minh hơn
- `.env.example`: thêm `.m4a,.mp3`, `PIPELINE_VISION_BATCH_SLEEP_SECONDS`
