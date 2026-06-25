# Plan Entry — BV Hưng Thịnh: Cloud theo phòng ban

## Mục tiêu

Mỗi phòng ban upload tài liệu lên Cloud → catalog tập trung → OCR/AI hỗ trợ tìm kiếm → cộng tác an toàn.

## PLAN — Cấu trúc OCIS

**Khuyến nghị:** 1 Project Space chính + thư mục theo phòng (đơn giản, dễ rollout):

```
BV-Hung-Thinh/          ← Project Space
├── 01-Ke-hoach-tong-hop/
├── 02-CDHA/
├── 03-Phu-san/
├── 04-Dieu-duong/
├── 05-To-chuc-can-bo/
├── 06-Phong-khac/...
└── _Quy-trinh-chung/
```

**Nâng cao (sau):** mỗi phòng một Project Space riêng nếu cần tách quyền chặt (RBAC độc lập).

| Bước | Việc | Owner |
|------|------|-------|
| P1 | Tạo Project Space `BV-Hung-Thinh` | IT / admin |
| P2 | Gán **Manager** mỗi phòng (trưởng phòng hoặc thư ký) | IT |
| P3 | Di chuyển/chuẩn hóa từ `/Yen` → cấu trúc phòng ban | HCNS + IT |
| P4 | Hướng dẫn phòng ban upload (web / desktop sync) | IT |
| P5 | `owncloud_sync_catalog.py` theo prefix phòng | Pipeline |
| P6 | OCR batch (PDF ưu tiên) → Postgres `markdown` | Pipeline |
| P7 | `ai_enrich_documents.py` gắn `ai_category`, `ai_tags` theo phòng | Pipeline |
| P8 | Webapp / query FTS theo phòng + tag | UI |

## PLAN — Metadata & AI

| Trường | Nguồn | Ví dụ |
|--------|-------|-------|
| `owncloud_path` | OCIS sync | `/BV-Hung-Thinh/05-To-chuc-can-bo/...` |
| `ai_category` | DeepSeek enrich | `hop-dong-lao-dong`, `quyet-dinh` |
| `ai_tags` | DeepSeek + verified | `CDHA`, `2024`, `nhan-su` |
| `verified_metadata` | Phòng ban xác nhận | JSON backfill thủ công |

Luồng: **lọc thô (phòng + loại file)** → **AI chỉ trên subset** → human verify mẫu quan trọng.

## PLAN — Collaboration

- Editor: nhân viên phòng upload/sửa trong thư mục phòng mình.
- Manager: trưởng phòng mời thành viên, không xóa space khi người rời.
- Viewer: lãnh đạo / phòng liên quan chỉ đọc (nếu cần).

## CHECK

- [ ] Project Space `BV-Hung-Thinh` tạo xong, ≥1 phòng có Manager
- [ ] Phòng thử nghiệm (vd. Tổ chức cán bộ) upload ≥10 file
- [ ] Sync Postgres: `owncloud_path` + `status=cataloged`
- [ ] OCR ≥5 PDF thành công, FTS tìm được từ khóa
- [ ] AI enrich gắn đúng phòng/loại văn bản
- [ ] Chính sách: phòng nào được phép dùng AI trên loại tài liệu nào

## ACT

- Nếu phòng ngại upload: desktop ownCloud client sync thư mục local ↔ OCIS.
- Nếu lo ngại bảo mật: tách space lâm sàng vs hành chính; AI chỉ chạy zone hành chính trước.
