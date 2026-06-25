# Memory Entry — OCIS Shared Drive / Project Spaces

## Câu hỏi

Có thể có Shared Drive giống Google Drive hay SharePoint Microsoft không?

## Kết luận ngắn

**Có.** Trên ownCloud Infinite Scale (OCIS), khái niệm tương đương là **Spaces**, đặc biệt **Project Space** (`driveType: project`).

| Nền tảng | Tương đương team-owned |
|----------|------------------------|
| Google Workspace | Shared Drive |
| Microsoft 365 | SharePoint site / document library |
| **OCIS** | **Project Space** |

## Ba loại Space chính

1. **Personal Space** — nhà riêng từng user (`personal/admin`). Hiện thư mục `/Yen` đang nằm đây.
2. **Project Space** — kho nhóm/dự án; file **không gắn một user**; thành viên rời đi thì dữ liệu vẫn còn.
3. **Shares** — khu vực ảo chứa share nhận từ người khác.

API thiết kế theo **Microsoft Graph** (`/graph/v1beta1/me/drives`); mỗi space trả `webDavUrl` riêng.

## Khuyến nghị cho OCR pipeline

- Dùng **Project Space** (vd. `OCR-HADE` hoặc `Yen-Team`) làm SoT file thay vì chỉ Personal `/Yen`.
- Personal giữ file riêng; Project Space dùng cho đồng bộ catalog + OCR + phân quyền team.
- Script `owncloud_sync_catalog.py` hiện sync qua `/remote.php/dav/files/admin/` — với Project Space cần prefix WebDAV từ Graph API (`/dav/spaces/{drive-id}`).

## Trạng thái instance local (2026-06-25)

`GET /graph/v1beta1/me/drives` → chỉ có `personal/admin` và `virtual/shares`; **chưa có Project Space**.
