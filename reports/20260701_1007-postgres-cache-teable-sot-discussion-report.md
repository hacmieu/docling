# Báo cáo thảo luận — Postgres cache, Teable SoT

**Ngày:** 2026-07-01 10:07

## Bối cảnh

Yêu cầu: **Postgres chỉ là CACHE**, **Teable là SoT**. Cần luồng hợp lý, khoa học, tối ưu.

Quan sát thực tế: `/search` nhanh vì đọc Postgres local; `/teable` chậm hơn vì Teable REST — xác nhận đúng nghi ngờ của user.

## Kết luận ngắn

| Câu hỏi | Trả lời |
|---------|---------|
| Search có đang dùng Postgres? | **Có** — `llm_context_pack.py` → `db_postgres.connect` |
| Teable có phải SoT trên UI? | **Chỉ `/teable`** — `/search` chưa |
| Postgres nên là gì? | **Staging pipeline + read cache derive từ Teable** |
| Có nên bỏ Postgres? | **Không** — OCR markdown, batch, multi-version cần local |

## Mô hình đề xuất: CQRS nhẹ

**Command side (ghi):**

- Pipeline ghi Postgres (staging).
- Publish đẩy lên Teable (sự kiện duy nhất làm metadata "chính thức").
- Human sửa Teable → đồng bộ ngược cache Postgres.

**Query side (đọc):**

- PCN / LLM / filter: **Teable** (trực tiếp hoặc qua cache đã sync từ Teable).
- Dev/debug OCR raw: Postgres tab riêng, không gọi là catalog SoT.

```text
                    ┌─────────────┐
  OwnCloud files ──►│  Postgres   │─── OCR / enrich / draft
                    │  (staging)  │
                    └──────┬──────┘
                           │ publish
                           ▼
                    ┌─────────────┐
  PCN sửa metadata ◄│   Teable    │─── SoT metadata
                    │   (SoT)     │
                    └──────┬──────┘
                           │ webhook / poll
                           ▼
                    ┌─────────────┐
                    │  Postgres   │─── read cache (optional fast path)
                    │  (mirror)   │
                    └─────────────┘
```

## So sánh 3 hướng đọc Search

| Hướng | Tốc độ | Đúng SoT | Ghi chú |
|-------|--------|----------|---------|
| Postgres trực tiếp (hiện tại) | Nhanh nhất | Không | Phù hợp dev tạm |
| Teable API mỗi request | Chậm hơn | Có | Đơn giản, đã có `/teable` |
| Teable + Postgres cache + webhook | Nhanh sau warm | Có | **Khuyến nghị production** |

## Rủi ro nếu giữ Postgres làm SoT ngầm

1. PCN sửa Teable → Search/LLM vẫn trả dữ liệu cũ từ Postgres.
2. Hai nguồn lệch nhau không có `published_at` / conflict rule.
3. Teable ERD chuẩn hóa (OwnCloud / DocExtractions) bị bypass.

## Hiện trạng code (2026-07-01)

| Thành phần | Nguồn | Ghi chú |
|------------|-------|---------|
| `/search` API | Postgres | `search_context_pack` |
| `/teable` API | Teable | `teable_read.py` — mới |
| `/` catalog | Postgres | Pipeline view |
| Sync pipeline | PG → Teable | `teable_incremental_sync`, scripts |
| Sync ngược | Chưa | Gap chính |

## Lộ trình đề xuất (tóm tắt)

1. **Ngay:** Document + env `CATALOG_SOT=teable` (policy).
2. **Tuần 1:** `/search` đọc Teable (`teable_search.py`).
3. **Tuần 2:** Publish contract + `published_to_teable_at`.
4. **Tuần 3:** Webhook Teable → cache Postgres.
5. **Tuần 4:** `CATALOG_READ_MODE=cache` nếu webhook ổn.

Chi tiết: [plans/20260701_1007-teable-sot-workflow-architecture-plan.md](../plans/20260701_1007-teable-sot-workflow-architecture-plan.md)

## Cần quyết định thêm

- Tần suất sync Teable → cache: realtime webhook vs poll 5 phút.
- Có ẩn tab Postgres với user PCN hay chỉ đổi nhãn "Pipeline cache".
- Search degrees (177 doc) trên Teable: cần index/view Teable hay scan API (chậm hơn staff 7 doc).
