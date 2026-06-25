# Report — Tư vấn Shared Drive trên OCIS

## Tóm tắt

OCIS **có** mô hình Shared Drive qua **Project Spaces**. Đây là tính năng cốt lõi của Infinite Scale, API theo Microsoft Graph, phù hợp thay Google Shared Drive / SharePoint document library trong stack OCR self-hosted.

## So sánh chi tiết

| Tiêu chí | Google Shared Drive | SharePoint | OCIS Project Space |
|----------|--------------------|------------|-------------------|
| Sở hữu | Team / org | Site collection | Space (project) |
| File khi user rời | Giữ lại | Giữ lại | Giữ lại |
| Phân quyền | Viewer…Manager | SP groups/roles | Manager, Editor, … |
| API | Drive API | Microsoft Graph | LibreGraph / Graph-compatible |
| WebDAV sync | Hạn chế | Có | Có (`webDavUrl` per space) |
| Desktop client | Drive for desktop | OneDrive sync | ownCloud desktop |

## Trạng thái hiện tại (instance `127.0.0.1:9200`)

- Đang dùng **Personal Space** `admin` — thư mục `/Yen`, **477 file** đã sync Postgres.
- **Chưa** tạo Project Space.
- Graph API xác nhận: `personal/admin`, `virtual/shares` only.

## Khuyến nghị triển khai

1. Tạo Project Space `OCR-HADE` trên UI hoặc Graph API.
2. Đưa (hoặc sync) tài liệu OCR vào space đó thay vì chỉ Personal.
3. Mở rộng `owncloud_sync_catalog.py` để đọc `webDavUrl` từ Graph khi sync Project Space.
4. Giữ Postgres làm catalog/index; OCIS làm file SoT.

## Tham chiếu

- [ownCloud Spaces feature](https://owncloud.com/features/spaces/)
- [Graph Spaces API](https://owncloud.dev/apis/http/graph/spaces/)
- [ADR-0007 Spaces API](https://owncloud.dev/ocis/adr/0007-api-for-spaces/)
