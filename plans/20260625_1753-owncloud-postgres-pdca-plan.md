# Plan Entry - OwnCloud + PostgreSQL PDCA (Plan / Check / Act)

## PLAN

| # | Mục tiêu | Deliverable |
|---|----------|-------------|
| P1 | OwnCloud local | `infra/docker-compose.yml` (port 8088) |
| P2 | PostgreSQL SoT | `ocr_catalog` on port 5433 + schema tags/categories/verified |
| P3 | Sync đường dẫn file | `scripts/owncloud_sync_catalog.py` |
| P4 | Migrate SQLite → PG | `scripts/migrate_sqlite_to_postgres.py` |
| P5 | AI gán nhãn | `scripts/ai_enrich_documents.py` (doc_type, category, tags, key_fields) |
| P6 | Backdate verified | `scripts/import_verified_metadata.py` + sample JSON |

## DO (đã triển khai)

1. `docker compose up -d` → Postgres + OwnCloud.
2. Migrate 23 documents từ SQLite active DB sang PostgreSQL.
3. Chuẩn bị manifest mẫu cho verified backfill.

## CHECK (bạn chạy sau khi đẩy SoT lên OwnCloud)

- [ ] OwnCloud UI mở được: http://127.0.0.1:8088
- [ ] Upload/copy file vào folder `/OCR` trên OwnCloud
- [ ] `owncloud_sync_catalog.py --remote-prefix /OCR` → rows tăng trong `documents`
- [ ] OCR ingest file mới (hash đổi) → `status=success`
- [ ] `ai_enrich_documents.py` → `ai_category`, `ai_tags`, `ai_key_fields` có dữ liệu
- [ ] `import_verified_metadata.py` → `verified_metadata` + `verified_at` backdate
- [ ] Query thô: filter theo tag/category trước khi gọi AI Q&A

## ACT (vòng tiếp theo)

- Chuẩn hóa taxonomy tag/category (bảng `tags`, `categories`).
- Cập nhật webapp đọc PostgreSQL thay SQLite.
- Chỉ re-enrich doc có `source_sha256` thay đổi hoặc `ai_review_status=failure`.
- Tách API key Codex nếu cần pipeline đọc ảnh trực tiếp.
