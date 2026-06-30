# Plan: Triển khai Google Vision song song

**Thời điểm:** 2026-06-30 08:10

## Mục tiêu

Chạy full vision batch (`gemini-2.5-flash`) song song với Teable sync loop đang hoạt động; không chạm lane enrich (đã xong 498/498).

## Thiết kế song song

| Lane | Process | API | Trạng thái |
|------|---------|-----|------------|
| Teable sync | loop 5 phút (từ 29/06) | Teable API | ✅ Đang chạy |
| Google Vision | `run_vision_batch_sync.py` nền | `GOOGLE_API_KEY` | 🚀 Khởi động 30/06 |
| AI enrich | — | AI Box | ✅ Hoàn tất |

## Tham số batch

```bash
uv run python scripts/run_vision_batch_sync.py \
  --sleep-seconds 12 \
  --skip-existing \
  --log-file workspace/ocr_pipeline/09_logs/20260630_0810-vision-batch.log
```

- **444 doc** trong queue (470 success − 3 pilot − 23 thiếu `local_path` hoặc ngoài prefix)
- Nhịp **12s/doc** ≈ ~5 req/phút (free-tier)
- ETA ≈ **2.5–3.5 giờ**

## Sau khi batch xong

1. `recompute_effective_metadata.py --sync-teable` — chuyển effective sang `google_vision`
2. Teable loop tự pick up extractions mới (hoặc chạy sync thủ công một lần)
3. Ghi báo cáo SLA `20260630_*-vision-batch.json`

## Rủi ro

- **429 quota** — script có retry trong `vision_tasks`; nếu fail hàng loạt, tăng `--sleep-seconds` lên 15–20
- Log bị duplicate dòng do redirect stdout → cùng log-file (không ảnh hưởng kết quả)
