# Report — Tư vấn Teable thay SPA custom

## Tóm tắt

Dùng **Teable** làm giao diện bảng (list + detail + filter + phân quyền) **khả thi** và phù hợp BV Hưng Thịnh. **Không** thay Postgres catalog; **đồng bộ một chiều** Postgres → Teable qua REST API.

## So sánh

| | Custom `pg_app.py` | **Teable** |
|--|-------------------|------------|
| List/detail | Tự code | Grid, gallery, kanban sẵn |
| Filter/group | Hạn chế | View + filter mạnh |
| Phân quyền phòng | Tự làm | Role Teable |
| Form nhập metadata | Không | Form view |
| Bảo trì FE | Cao | Thấp (cấu hình) |
| SoT | Postgres | Postgres (Teable chỉ mirror) |

## Teable KHÔNG làm được (hiện tại)

- Trỏ Teable trực tiếp vào DB `ocr_catalog` port 5433
- Thay Postgres pipeline bằng DB nội bộ Teable

## Bạn cần chuẩn bị trên Teable

1. **Space/Base** `HTH-OCR-Catalog`
2. **Bảng + cột** (schema ở plan)
3. **API token** + `baseId`, `tableId`
4. **Views** theo trạng thái OCR / phòng ban
5. **User/role** cho từng phòng (tuỳ chính sách BV)

## Bước kế (repo)

Sau khi bạn gửi `TEABLE_*` trong `.env`, implement `sync_catalog_to_teable.py` pilot 10–50 dòng.

## Tham chiếu

- [Teable Create records API](https://help.teable.ai/en/api-reference/record/create-records)
- Local instance: http://127.0.0.1:3010
