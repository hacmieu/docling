# Báo cáo — Giao diện tìm kiếm + DeepSeek

**Ngày:** 2026-06-30

## Tính năng

1. **Chế độ nhân sự** — tìm theo tên (VD: Trần Đức Hiển)
2. **Chế độ bằng/chứng chỉ** — toàn catalog hoặc lọc BÁC SĨ
3. **Hiển thị** — bảng doc_id, doc_type, key_fields, summary
4. **Tokens** — `~N tokens (prompt)` trước khi gọi AI
5. **Nút DeepSeek** — POST synthesize, hiển thị câu trả lời

## Khởi chạy

```bash
uv run python workspace/ocr_pipeline/webapp/pg_app.py --port 8766
```

Mở: http://127.0.0.1:8766/search

## Luồng

```text
Tìm kiếm → /api/search/context → hiển thị + tokens
         → nhập câu hỏi → Gửi DeepSeek → /api/search/synthesize → answer
```
