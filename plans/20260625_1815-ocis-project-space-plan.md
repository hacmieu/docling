# Plan Entry — OCIS Project Space (Shared Drive) cho OCR

## Mục tiêu

Có kho file nhóm giống Google Shared Drive / SharePoint, làm nguồn file chính cho pipeline OCR.

## PLAN

| Bước | Việc | Ghi chú |
|------|------|---------|
| P1 | Tạo Project Space trên OCIS | UI: **Files → Spaces → Create** hoặc Graph `POST /graph/v1.0/drives` body `{"name":"OCR-HADE","driveType":"project"}` |
| P2 | Upload / di chuyển batch `Yen` | Giữ cấu trúc thư mục con (2.CĐHA, 7.PHỤ SẢN, …) |
| P3 | Mời thành viên | Role **Manager** / **Editor** theo team |
| P4 | Cập nhật sync script | Hỗ trợ `--space-id` hoặc `--remote-prefix` theo `webDavUrl` của Project Space |
| P5 | Sync → Postgres → OCR | `status=cataloged` → ingest PDF → `ai_enrich_documents.py` |

## So sánh lựa chọn

| Phương án | Ưu | Nhược |
|-----------|-----|-------|
| Giữ Personal `/Yen` | Đã có 477 file, sync chạy được | Gắn tài khoản `admin`; khó chia sẻ team |
| **Project Space mới** | Team-owned, đúng mô hình Shared Drive | Cần tạo space + chỉnh sync |
| Share folder từ Personal | Nhanh | Vẫn owner là user; không bền bằng Project Space |

**Khuyến nghị:** Project Space `OCR-HADE` (hoặc `Yen-OCR`).

## CHECK

- [ ] Project Space xuất hiện trong UI sidebar **Spaces**
- [ ] `GET /graph/v1beta1/me/drives` có entry `driveType: project`
- [ ] WebDAV PROPFIND trên `webDavUrl` của space trả file
- [ ] `owncloud_sync_catalog.py` sync được vào Postgres
- [ ] Quyền thành viên: thêm/xóa user không mất file

## ACT nếu kẹt

- Admin không thấy nút tạo Space → vào **Files → Spaces** (không phải Admin Settings)
- Hoặc gán role **Space Admin** cho user cần tự tạo space (quyền rộng — cân nhắc bảo mật)
