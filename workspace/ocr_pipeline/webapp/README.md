# OCR Pipeline Webapps

Lightweight browsers for OCR catalog data.

| App | Backend | Port | UI |
|-----|---------|------|-----|
| `app.py` | SQLite (`08_sqlite/`) | **8765** | Sidebar list |
| **`pg_app.py`** | **PostgreSQL** (`ocr_catalog`) | **8766** | **Table list → detail** |

## PostgreSQL catalog (khuyến nghị)

```bash
# Đảm bảo Postgres đang chạy
cd workspace/ocr_pipeline/infra && docker compose up -d ocr-postgres

# Chạy webapp
uv run python workspace/ocr_pipeline/webapp/pg_app.py --host 127.0.0.1 --port 8766
```

Mở: **http://127.0.0.1:8766**

- Bảng danh sách: ID, file, đường dẫn OCIS, status, OCR, AI, category
- Click dòng → panel detail: markdown, AI metadata, verified fields
- Lọc: status, drive (`HTH-Shared-Drive`, `/Yen`), tìm kiếm path
- Phân trang 50 dòng/trang

Cần `.env` với `OCR_DATABASE_URL` (mặc định `postgresql://ocr:ocr@127.0.0.1:5433/ocr_catalog`).

## SQLite viewer (legacy)

```bash
uv run python workspace/ocr_pipeline/webapp/app.py --host 127.0.0.1 --port 8765
```

## Port check

```bash
uv run python workspace/ocr_pipeline/webapp/pg_app.py --port 8766 --check-port-only
```
