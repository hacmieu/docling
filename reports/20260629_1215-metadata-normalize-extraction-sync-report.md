# Report — Chuẩn hóa + migrate DocExtractions (RAW & DeepSeek)

## Yêu cầu

1. Migrate dữ liệu sang **DocExtractions**: bản **RAW** (OCR) và **DeepSeek AI**
2. Dùng đúng **Teable field types** cho `ai_tags`, `ai_doc_type`, `ai_category`
3. Chuẩn hóa hoa/thường — đặc biệt category và doc_type

## Chuẩn hóa

### Vấn đề trước đó

| ai_category | ai_doc_type |
|-------------|-------------|
| `nhân sự` / `Nhân sự` / `Hành chính nhân sự` | `Quyết định` / `quyết định` |
| `lao động` / `Hợp đồng lao động` | `so_ho_khau` / `hợp đồng lao động` |

### Quy ước sau normalize

- **ai_category**: nhãn VN chuẩn — `Nhân sự`, `Hợp đồng lao động`, `Quyết định`…
- **ai_doc_type**: slug — `nhan-su`, `hop-dong-lao-dong`, `quyet-dinh`…
- **ai_tags**: slug — `dao-tao`, `hop-dong`, `nhan-su`…

Module: `metadata_normalize.py` + `config/taxonomy_vi.json`

## Teable field upgrade

Đã **xóa** field text cũ và tạo lại:

| Bảng | ai_category | ai_doc_type | ai_tags |
|------|-------------|-------------|---------|
| OwnCloud | singleSelect (8) | singleSelect (7) | multipleSelect (24) |
| DocExtractions | singleSelect (8) | singleSelect (7) | multipleSelect (24) |

Script: `upgrade_teable_metadata_fields.py`

API dùng: `DELETE /table/{id}/field/{id}`, `POST /table/{id}/field`

## Migrate DocExtractions

| Metric | Giá trị |
|--------|---------|
| Rows synced | **462** (HTH-Shared) |
| RAW (`local_llm_ocr`) | ~424 rows — chỉ `raw_text_preview` |
| DeepSeek (`deepseek_cleanup`) | ~38 rows — full AI metadata |
| Link → OwnCloud | `document: {"id": "rec..."}` |
| Thời gian | ~250s |

Script: `sync_extractions_to_teable.py`

### Ví dụ doc_id 503

| Version | source | ai_category | ai_doc_type | ai_tags |
|---------|--------|-------------|-------------|---------|
| RAW-v1 | local_llm_ocr | — | — | — |
| DeepSeek-v2 | deepseek_cleanup | Hợp đồng lao động | hop-dong-hoc-viec | dao-tao, hoc-viec, hop-dong, lao-dong |

## OwnCloud resync

475 row PATCH với giá trị đã chuẩn hóa + multipleSelect tags.

## Lệnh vận hành

```bash
uv run python scripts/normalize_catalog_metadata.py
uv run python scripts/upgrade_teable_metadata_fields.py
uv run python scripts/sync_catalog_to_teable.py
uv run python scripts/sync_extractions_to_teable.py
```

## Verdict

DocExtractions trên Teable đã có **2 tầng phiên bản** (RAW + DeepSeek), metadata **chuẩn hóa**, field types **đúng Teable**.
