# Plan — Đẩy dữ liệu vào Teable liên tục

1. Giữ lane xử lý OCR/AI enrich trên Postgres để ổn định transaction.
2. Chạy đồng bộ Teable theo vòng lặp 5 phút:
   - `sync_extractions_to_teable.py`
   - `recompute_effective_metadata.py --sync-teable`
3. Kiểm tra log loop:
   - `workspace/ocr_pipeline/09_logs/20260629_1552-teable-sync-loop.log`
4. Khi enrich batch kết thúc:
   - chạy một vòng sync full cuối để chốt dữ liệu Teable.
