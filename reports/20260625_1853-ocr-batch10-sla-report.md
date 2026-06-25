# Report — OCR pilot 10 file (SLA)

## Kết quả

| Metric | Giá trị |
|--------|---------|
| Batch bắt đầu | 2026-06-25T11:51:51Z |
| Batch kết thúc | 2026-06-25T11:53:30Z |
| **Tổng thời gian** | **98.9 giây** |
| File xử lý | 10 PDF |
| Thành công | **10/10** |
| Trung bình/file | **9.9 giây** |
| Engine | EasyOCR vi,en (full-page) |

## Chi tiết từng file

| ID | Thời gian (s) | md_len |
|----|---------------|--------|
| 503 | 17.0 | 3263 |
| 504 | 17.1 | 7033 |
| 505 | 18.5 | 7609 |
| 506 | 3.9 | 1242 |
| 507 | 3.2 | 327 |
| 508 | 5.7 | 1308 |
| 509 | 16.3 | 3228 |
| 510 | 4.6 | 1533 |
| 511 | 5.7 | 2010 |
| 513 | 6.8 | 2320 |

## Artifacts

- SLA JSON: `workspace/ocr_pipeline/09_logs/20260625_1853-ocr-sla.json`
- Log chạy: `workspace/ocr_pipeline/09_logs/20260625_1850-ocr-batch10.log`
- Script: `scripts/ocr_catalog_postgres.py`

## Xem trên webapp

http://127.0.0.1:8766 — lọc status `success`, cột OCR > 0.
