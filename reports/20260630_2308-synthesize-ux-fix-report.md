# Báo cáo — Sửa DeepSeek tổng hợp + tokens trước gửi

**Ngày:** 2026-06-30

## Vấn đề

Kết quả "cần câu hỏi cụ thể" khiến user nghi prompt không chạy hoặc dữ liệu không được đẩy vào.

## Thực tế

API với context đầy đủ (~811 tokens) **hoạt động** khi test backend. Lỗi UX:

- Không xem/sửa context trước gửi
- Nút Gửi bật khi chưa có dữ liệu
- Prompt model chưa đủ chặt

## Cải tiến UI

1. **Panel ~tokens** — tách câu hỏi / context / số doc
2. **Textarea Context** — hiện metadata sau Tìm kiếm, sửa để bớt tokens
3. **Checkbox từng dòng** — bỏ doc không cần → rebuild context
4. Nút Gửi chỉ bật khi ≥1 doc và context ≥80 ký tự

## Luồng đúng

```text
Tìm kiếm → xem context + tokens → (tuỳ chọn bớt doc/dòng) → Gửi DeepSeek
```

Hard refresh: http://127.0.0.1:8766/search
