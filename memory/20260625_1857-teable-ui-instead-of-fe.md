# Memory Entry — Teable thay custom FE

## Câu hỏi

Đẩy catalog OCR lên Teable thay vì viết frontend — cần gì ở Teable?

## Kết luận

- **Teable không mount trực tiếp** Postgres `ocr_catalog` (5433) làm nguồn như NocoDB. Teable dùng **DB riêng** (instance local port 3010 / postgres 5432).
- **SoT giữ nguyên:** OCIS (file) + Postgres (catalog/OCR/AI). Teable = **lớp UI/quản trị** đồng bộ qua **API**.
- Instance local đang có: http://127.0.0.1:3010

## Cần từ phía Teable (user/IT)

1. **Base** mới: vd. `HTH-OCR-Catalog`
2. **Bảng `documents`** với cột khớp pipeline (xem plan)
3. **Personal Access Token** + `baseId`, `tableId`
4. **Views:** theo phòng ban, status OCR, chưa AI enrich
5. **Phân quyền** theo phòng (Manager/Editor/Viewer)
6. (Tuỳ chọn) **Form view** để phòng ban nhập `verified_metadata`

## Pipeline đề xuất

```
OCIS → sync → Postgres (SoT) → script API → Teable (UI)
```

Không bỏ Postgres; Teable sync định kỳ hoặc sau OCR/AI batch.
