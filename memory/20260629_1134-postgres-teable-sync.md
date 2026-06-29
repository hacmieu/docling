# Memory — Postgres 4 bảng + Teable sync noibo

## Postgres `ocr_catalog` — **4 bảng**

| Bảng | Vai trò |
|------|---------|
| `documents` | SoT: path, OCR markdown, AI metadata, verified |
| `tags` | Từ điển tag |
| `categories` | Từ điển category |
| `document_tags` | Nối doc ↔ tag (M:N) |

## Teable (UI mirror)

- Base: `https://noibo.hungthinh.hospital`, table `OwnCloud` (`tblNwc8A1llcPa0JcsA`).
- Hiện chỉ 3 cột: **Label**, **Number** (doc_id), **Status** (To do / In progress / Done).
- Sync `scripts/sync_catalog_to_teable.py`: 475 row HTH-Shared, ~223s, 0 lỗi.
- Token trong `.env` (gitignored).

## Hạn chế

Bảng Teable chưa có cột path đầy đủ, markdown, ai_tags — cần thêm field trên Teable rồi mở rộng script.
