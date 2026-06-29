# Plan: So sánh model vision & 4 phiên bản extraction

**Thời điểm:** 2026-06-29 17:48

## Mục tiêu

Xác nhận `gemini-1.5-pro` có dùng được không; xuất kết quả so sánh 4 phiên bản cho user.

## Đã thực hiện

- [x] ListModels + probe `gemini-1.5-pro`, `gemini-1.5-pro-latest`, `gemini-2.5-pro`
- [x] Trích xuất 3 doc pilot (503–505) từ `document_extractions`
- [x] Ghi JSON + báo cáo markdown

## Kết quả

| Hạng mục | Kết quả |
|----------|---------|
| gemini-1.5-pro | ❌ 404 — bỏ qua |
| gemini-2.5-pro | ⚠️ 429 — chờ quota |
| So sánh 3 lane + slot pro | ✅ Báo cáo `reports/20260629_1748-four-version-ocr-comparison-report.md` |

## Bước tiếp (tùy chọn)

1. Nâng quota Google → pilot `gemini-2.5-pro` 5 doc, lưu extraction riêng.
2. Tiếp tục full vision batch ~447 doc với `gemini-2.5-flash` (nhịp chậm tránh 429).
3. Không lên kế hoạch migrate sang 1.5 — model không còn trên API.
