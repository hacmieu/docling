# Report — Full OCR batch SLA (HTH-Shared-Drive)

## Kết quả

| Metric | Giá trị |
|--------|---------|
| Batch bắt đầu | 2026-06-25T13:58:03Z |
| Batch kết thúc | 2026-06-25T15:16:15Z |
| **Tổng thời gian** | **4692 giây (~78.2 phút)** |
| File batch này | 437 PDF |
| Thành công | **437/437** |
| Thất bại | 0 |
| **TB/file** | **10.7 giây** |
| Engine | EasyOCR vi,en full-page |

## Tổng HTH-Shared trong Postgres

| Status | Số |
|--------|-----|
| success (OCR) | **447** |
| cataloged (chưa OCR) | 28 (docx/m4a/…) |

## SLA artifacts

- `workspace/ocr_pipeline/09_logs/20260625_2056-ocr-full-sla.json`
- `workspace/ocr_pipeline/09_logs/20260625_2056-ocr-full-batch.log`

## ENV Teable

Đã để sẵn trong `.env` (token/base/table để trống — chưa chuyển UI).

## SLA gợi ý vận hành

- PDF scan A4 ~1–3 trang: ~4–18s (pilot)
- Full batch TB: **~10.7s/PDF**
- Ước lượng 500 PDF: **~89 phút** single-thread EasyOCR trên máy hiện tại
