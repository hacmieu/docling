# Playbook — Postgres = CACHE, Teable = SoT

**Ngày:** 2026-07-01 10:07

## Quyết định (làm rõ)

| Khái niệm | Vai trò | Không được |
|-----------|---------|------------|
| **Teable** | SoT metadata đã publish + human verify | Coi là mirror phụ |
| **Postgres** | **Cache + staging pipeline** | SoT tra cứu PCN / LLM / filter |
| **OwnCloud** | SoT file gốc (binary) | — |

Postgres **không** mất — nhưng chỉ hai việc:

1. **Staging:** OCR markdown, `document_extractions` draft/active trước khi publish.
2. **Read cache (tuỳ chọn):** bản sao metadata từ Teable để query nhanh; **Teable thắng khi lệch**.

## Vì sao `/search` nhanh hôm nay

`/search` gọi `llm_context_pack` → `connect()` Postgres trực tiếp. **Chưa đọc Teable.** Đó là lý do nhanh nhưng **sai SoT**.

`/teable` chậm hơn vì REST + phân trang API — đúng nguồn SoT.

## Luồng chuẩn (CQRS đơn giản)

```text
WRITE (pipeline):
  OC file → Postgres staging → enrich → PUBLISH → Teable

WRITE (human):
  Teable sửa → webhook/poll → Postgres human_verified (cache/staging đồng bộ)

READ (user / LLM):
  Teable API  ──hoặc──►  Postgres read-cache (derive từ Teable, TTL/webhook)
  Postgres raw OCR     ──chỉ──►  tab debug / pipeline (không hiển thị PCN)
```

## Quy tắc xung đột

1. Metadata **đã publish** trên Teable: **Teable thắng** mọi lúc.
2. Row Postgres `draft` / đang chạy batch: **không** ghi đè Teable.
3. Publish = sự kiện rõ ràng (`published_to_teable_at` + `teable_record_id`).
4. Cache Postgres invalidate khi: publish mới, webhook Teable, hoặc `cache_synced_at` quá TTL.

## Env định hướng

```bash
CATALOG_SOT=teable
CATALOG_READ_MODE=teable          # teable | cache (cache vẫn derive từ Teable)
CACHE_SYNC=webhook                # webhook | poll | on_publish_only
```

## Liên kết

- Plan: [plans/20260701_1007-teable-sot-workflow-architecture-plan.md](../plans/20260701_1007-teable-sot-workflow-architecture-plan.md)
- Report: [reports/20260701_1007-postgres-cache-teable-sot-discussion-report.md](../reports/20260701_1007-postgres-cache-teable-sot-discussion-report.md)
