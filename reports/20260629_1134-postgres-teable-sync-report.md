# Report — Postgres schema + Teable sync triển khai

## Câu hỏi

DB hiện tại có mấy bảng? Đẩy catalog lên Teable noibo được chưa?

## Postgres: **4 bảng**

1. **`documents`** — bảng chính (~25 cột): path OCIS, `markdown` OCR, `status`, `ai_category`, `ai_tags`, `ai_key_fields`, `verified_metadata`, `doc_json` (SLA), …
2. **`tags`** — tên tag chuẩn hóa
3. **`categories`** — tên category
4. **`document_tags`** — liên kết document ↔ tag

Index đáng chú ý: FTS GIN trên `markdown`, unique `owncloud_path`.

## Teable: triển khai được — **đã sync**

| Metric | Giá trị |
|--------|---------|
| API | `https://noibo.hungthinh.hospital/api` |
| Table | OwnCloud `tblNwc8A1llcPa0JcsA` |
| Rows synced | **475** (HTH-Shared-Drive) |
| Thời gian | **223s** (~0.47s/row) |
| Created / Updated | 465 / 10 |
| Failed | 0 |

Script: `scripts/sync_catalog_to_teable.py`

```bash
uv run python scripts/sync_catalog_to_teable.py          # full upsert
uv run python scripts/sync_catalog_to_teable.py --limit 10  # pilot
```

## Lưu ý schema Teable

Bảng OwnCloud hiện chỉ **3 field mẫu** (Label, Number, Status). MVP map:

- **Label**: tên file + category AI (nếu có)
- **Number**: `doc_id` Postgres (key upsert)
- **Status**: pipeline stage (To do → In progress → Done)

**Chưa sync** lên Teable: full path, markdown, tags JSON, OCR SLA — cần user thêm cột trên Teable UI rồi bổ sung env `TEABLE_FIELD_*`.

## Git

- Token **không** commit — chỉ `.env` local.
- Script `sync_catalog_to_teable.py` commit lên `develop`.

## Verdict

- Lưu trữ đầy đủ: **Postgres 4 bảng** (SoT).
- UI nhân viên: **Teable đã có 475 dòng**; mở rộng cột để đủ nhu cầu tìm kiếm/phạm vi hành nghề.
