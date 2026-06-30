# Báo cáo — Teable là Single Source of Truth

**Ngày:** 2026-06-30

## Yêu cầu

> Điều kiện kiên quyết: **Teable là SoT.**

## Trả lời thẳng

| Câu hỏi | Trước đây (code hiện tại) | Theo policy mới |
|---------|---------------------------|-----------------|
| Search `/search` lấy data đâu? | **Postgres** | Phải **Teable** |
| Teable vai trò gì? | Mirror Postgres | **SoT metadata** |
| Postgres còn không? | SoT | **Engine pipeline**, không SoT tra cứu |

## Vì sao Teable làm SoT hợp lý

- PCN/hành chính đã quen filter, view, link bảng trên Teable
- Human verify (`human_verified`) xảy ra trên UI Teable
- Phân quyền, audit, chia sẻ view — Teable có sẵn

## Postgres vẫn cần (không bỏ)

- OCR markdown, multi-version extractions, Celery vision/enrich
- `effective_document_extractions` view — tính toán nội bộ trước khi **publish lên Teable**
- Không expose Postgres ra UI end-user

## Gap cần lấp

1. **`/search` đọc Postgres** — cần `teable_search` + đổi `search_context_pack`
2. **Sync một chiều** Postgres→Teable — thiếu Teable→Postgres cho sửa tay
3. **`.env.example`** vẫn ghi "mirror" — cần `CATALOG_SOT=teable`

## Kiến trúc mục tiêu (tóm tắt)

```mermaid
flowchart LR
  subgraph pipeline [Pipeline]
    OC[OwnCloud] --> PG[(Postgres staging)]
    PG -->|publish| TB[(Teable SoT)]
  end
  subgraph users [Người dùng]
    TB --> UI[Teable UI]
    TB --> SRCH[/search API đọc Teable]
    UI -->|human edit| TB
    TB -->|webhook| PG
  end
```

## Bước tiếp theo (đề xuất)

1. Implement `teable_search.py` + flag `CATALOG_SOT=teable`
2. Chuyển `/api/search/context` sang Teable
3. Webhook human verify Teable → Postgres

Chi tiết: [plans/20260630_2315-teable-sot-migration-plan.md](../plans/20260630_2315-teable-sot-migration-plan.md)
