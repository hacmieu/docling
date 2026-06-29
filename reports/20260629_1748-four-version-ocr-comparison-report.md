# Báo cáo so sánh 4 phiên bản OCR / trích xuất

**Thời điểm:** 2026-06-29 17:48  
**Mẫu:** doc `503`, `504`, `505` (HĐ Đặng Thị Hồng Nhung — học việc / HĐLĐ)

## Kết luận nhanh

| Phiên bản | Model | Priority | Trạng thái |
|-----------|-------|----------|------------|
| **① local_llm_ocr** | docling-easyocr | 30 | ✅ Có sẵn (~447 doc) |
| **② deepseek_cleanup** | deepseek-v4-pro | 50 | ✅ Summary/metadata (không raw) |
| **③ google_vision** | gemini-2.5-flash | 70 | ✅ Pilot 3 doc — **effective winner** |
| **④ gemini-1.5-pro** | — | (dự kiến 70+) | ❌ **404** — không có trên API v1beta |
| *(thay thế pro)* gemini-2.5-pro | gemini-2.5-pro | — | ⚠️ **429 quota** — chưa chạy được OCR |

**gemini-1.5-pro không dùng được** với `GOOGLE_API_KEY` hiện tại: `ListModels` không liệt kê bất kỳ model `1.5-*` nào; gọi trực tiếp `generateContent` trả `404 models/gemini-1.5-pro is not found`.

Lane vision đang chạy ổn với **gemini-2.5-flash**. Nếu cần tier “pro”, dùng **gemini-2.5-pro** sau khi nâng quota/billing.

Dữ liệu JSON đầy đủ: `workspace/ocr_pipeline/09_logs/20260629_1748-four-version-comparison.json`

---

## Doc 503 — Hợp đồng học việc 26.02.2015

**Effective:** `google_vision` (priority 70)

### ① local_llm_ocr (EasyOCR) — raw 3263 ký tự

```
## CÔNG TY CP Y - DƯỢC IIƯNG THỊNH CỌỘNG HÒA XÃ IỘI CIỦ NGIA VIỆT NAM
Số: L6/HDHV HTT
Lào Cai. 26 02 ncum 2013 tháng ngà)
## HỢP ĐONG HỌC VIỆC
PHÙNG XUÂN THU — Quóc tich — Chứre vụ — Giám Đốc
DẠNG THỊ HONG NHUNG
```

Lỗi điển hình: `IIƯNG`, `L6` thay `16`, ngày `2013`, `HỢP ĐONG`, tên `DẠNG` thay `ĐẶNG`.

### ② deepseek_cleanup — summary 248 ký tự

> Hợp đồng học việc giữa Công ty CP Y Dược Hưng Thịnh và bà **Đặng Thị Hồng Nhung**, thời hạn 3 tháng từ 24/02/2015 đến 24/05/2015, vị trí Điều dưỡng. Cam kết làm việc tối thiểu 36 tháng sau học việc.

Không lưu full text; dùng cho category/tag/search.

### ③ google_vision (gemini-2.5-flash) — raw 1994 ký tự

```
CÔNG TY CP Y - DƯỢC HƯNG THỊNH
Số: 16/HĐHV – HT
Lào Cai, ngày 26 tháng 02 năm 2015
HỢP ĐỒNG HỌC VIỆC
ÔNG : PHÙNG XUÂN THU — ĐẶNG THỊ HỒNG NHUNG Sinh ngày: 20/07/1990
```

Chính tả và cấu trúc tốt nhất trong 3 lane có full text.

### ④ gemini-1.5-pro

Không chạy được (404). Không có excerpt để so sánh.

---

## Doc 504 — Hợp đồng lao động 15.01.2018

**Effective:** `google_vision`

| Lane | Điểm nổi bật |
|------|----------------|
| EasyOCR | `HỢP ĐỎNG`, ngày `ngàỵ/5 0/năm 2018`, tên công ty tách dòng lỗi |
| DeepSeek | Summary đúng: HĐLĐ không xác định thời hạn, P Điều dưỡng, từ 01/01/2018 |
| Gemini Flash | Header + số HĐ `34/HĐLĐ`, ngày `15 tháng 01 năm 2018` chuẩn |
| 1.5-pro | N/A |

---

## Doc 505 — Hợp đồng lao động 01.07.2024

**Effective:** `google_vision`

| Lane | Điểm nổi bật |
|------|----------------|
| EasyOCR | `176.$ IHTH`, `CÔNG TYCỔ PHẦN`, mất nhiều chữ giữa đoạn |
| DeepSeek | Ghi nhận “OCR kém với nhiều lỗi chính tả” — đúng với EasyOCR input |
| Gemini Flash | `176.8/HTH-HĐLĐ`, ngày `01 tháng 07 năm 2024`, đủ đoạn mở đầu Bộ luật Lao động |
| 1.5-pro | N/A |

---

## Bảng tổng hợp độ dài

| Doc | EasyOCR raw | DeepSeek sum | Gemini Flash raw |
|-----|-------------|--------------|------------------|
| 503 | 3263 | 248 | 1994 |
| 504 | 7033 | 201 | 1476 |
| 505 | 7609 | 205 | 1868 |

Gemini Flash cho text ngắn hơn EasyOCR nhưng sạch hơn; DeepSeek chỉ summary.

## Khuyến nghị

1. Giữ **gemini-2.5-flash** làm vision mặc định (`GOOGLE_VISION_MODEL`).
2. Không đặt kỳ vọng vào **gemini-1.5-pro** — đã sunset trên Generative Language API.
3. Nếu cần so sánh tier pro: bật quota **gemini-2.5-pro**, chạy pilot 5 doc, lưu `source_type=google_vision_pro` hoặc `model_name` riêng.
4. Waterfall hiện tại: `google_vision` > `deepseek_cleanup` > `local_llm_ocr` — phù hợp với kết quả mẫu.
