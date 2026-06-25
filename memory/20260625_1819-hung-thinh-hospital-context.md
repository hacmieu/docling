# Memory Entry — Bệnh viện Hưng Thịnh: Cloud cho phòng ban, AI & Collaboration

## Bối cảnh

Dự án phục vụ **Bệnh viện Hưng Thịnh (HTH)**: các phòng ban đưa tài liệu lên Cloud để tiện **AI** (OCR, phân loại, tìm kiếm) và **cộng tác** (chia sẻ, đồng bộ, không phụ thuộc một cá nhân).

## Dữ liệu hiện có (gợi ý mapping phòng ban)

Thư mục OCIS `/Yen` (477 file) đã phản ánh cấu trúc phòng ban:

| Thư mục OCIS | Phòng ban (ước lượng) |
|--------------|------------------------|
| `2.CĐHA` | Chẩn đoán hình ảnh |
| `7.PHỤ SẢN` | Phụ sản |
| `14.ĐIỀU DƯỠNG` | Điều dưỡng |
| HĐ, HSCN, QĐ, văn bằng… | Tổ chức cán bộ / HCNS |

## Định hướng kiến trúc

- **OCIS Project Spaces** = kho nhóm theo phòng (Shared Drive nội bộ).
- **PostgreSQL** = catalog (đường dẫn, tag phòng ban, OCR text, metadata AI).
- **AI chỉ trên tập đã lọc** (tag/phòng/FTS) — tiết kiệm chi phí API.
- **Collaboration** = quyền theo phòng trên OCIS; file không mất khi nhân sự luân chuyển.

## Lưu ý y tế

- Phân vùng: hồ sơ hành chính/nhân sự vs lâm sàng vs vận hành.
- Không đưa toàn bộ hồ sơ bệnh nhân vào AI hàng loạt nếu chưa có chính sách bảo mật/ẩn danh.
- Ưu tiên: quyết định, hợp đồng, quy trình, biểu mẫu — phù hợp OCR + metadata.
