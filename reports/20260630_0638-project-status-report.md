# Báo cáo tình trạng dự án OCR Catalog — BV Hưng Thịnh

**Thời điểm:** 2026-06-30 06:38 (local)  
**Branch:** `develop` @ `2208d4d7` (đồng bộ `origin/develop`)

---

## Tổng quan

| Hạng mục | Trạng thái | Chi tiết |
|----------|-----------|----------|
| Hạ tầng Docker | ✅ Ổn | Postgres OCR `:5433`, OCIS `:9200`, Teable stack healthy |
| Catalog Postgres | ✅ | **498** doc (470 OCR success + 28 cataloged chưa OCR) |
| OCR local (EasyOCR) | ✅ Xong | 470 doc có `local_llm_ocr` |
| AI enrich (DeepSeek) | ✅ ~xong | **487/498** success, **11** failure |
| Google Vision OCR | ⏳ Pilot | **3/470** doc (`gemini-2.5-flash`) |
| Teable sync loop | ✅ Đang chạy | Mỗi 5 phút, lần cuối ~23:34 UTC 29/06 |
| Vision batch full | ❌ Chưa chạy | ~447 doc còn lại |

---

## Postgres SoT (`ocr_catalog`)

### Documents

| status | count |
|--------|------:|
| success (đã OCR) | 470 |
| cataloged (chưa OCR) | 28 |
| **Tổng** | **498** |

### AI enrich (`ai_review_status`)

| status | count |
|--------|------:|
| success | 487 |
| failure | 11 |
| pending | 0 |

Batch full kết thúc **2026-06-29 13:31 UTC** (~2h 50m):

- processed: 454 | success: 443 | failure: 11 | skipped: 21
- avg: **18.2s/doc** | model: `deepseek-v4-pro`
- log: `workspace/ocr_pipeline/09_logs/20260629_1552-ai-enrich-full.log`

**11 doc lỗi** — chủ yếu mất mạng/DNS `api.ai-box.vn` (timeout, connection reset, name resolution). Cần retry khi API ổn định.

### Extraction versions (`document_extractions`)

| source_type | model | rows | docs |
|-------------|-------|-----:|-----:|
| local_llm_ocr | docling-easyocr | 470 | 470 |
| deepseek_cleanup | deepseek-v4-pro | 483 | 487 |
| deepseek_cleanup | gemini-3-flash | 4 | (legacy) |
| google_vision | gemini-2.5-flash | 3 | 3 |

### Effective metadata (waterfall)

| effective_source | count | Ghi chú |
|------------------|------:|---------|
| deepseek_cleanup | 484 | Đa số doc — vision chưa phủ |
| local_llm_ocr | 11 | Chưa có DeepSeek |
| google_vision | 3 | Doc 503, 504, 505 |

> Waterfall: `google_vision` (70) > `deepseek_cleanup` (50) > `local_llm_ocr` (30). Khi chạy full vision batch, effective sẽ chuyển sang Gemini trên các doc đó.

---

## API & lane xử lý

| Lane | Provider | Trạng thái |
|------|----------|-----------|
| Text enrich | AI Box / DeepSeek | ✅ Batch xong; 11 lỗi mạng |
| Vision OCR | Google `gemini-2.5-flash` | ✅ Probe OK (sample 1394 chars) |
| gemini-1.5-pro | — | ❌ 404 (không còn trên API) |
| gemini-2.5-pro | Google | ⚠️ 429 quota (chưa pilot) |

---

## Teable (`noibo.hungthinh.hospital`)

- Loop sync **đang chạy** (PID background từ 29/06 15:52).
- Mỗi vòng: sync 911 extractions (~10 phút) + patch 475 OwnCloud rows.
- Lần hoàn thành gần nhất trong log: `[LOOP] 2026-06-29T23:29:45Z sync done`.
- Log: `workspace/ocr_pipeline/09_logs/20260629_1552-teable-sync-loop.log`

---

## Việc còn lại (ưu tiên)

1. **Retry 11 doc enrich fail** — `ai_enrich_documents.py` filter `ai_review_status=failure`.
2. **OCR 28 doc `cataloged`** — chưa có markdown/local OCR.
3. **Vision batch ~467 doc** — `run_vision_batch_sync.py`, nhịp chậm tránh 429.
4. **Sau vision batch** — `recompute_effective_metadata.py --sync-teable` để Teable phản ánh Gemini làm nguồn chính.

---

## Git gần nhất

```
2208d4d7 Document gemini-1.5-pro unavailability and four-version OCR comparison.
a129ac13 Enable continuous Teable sync and fix select-option validation.
343b61c6 Switch vision OCR lane to Google Gemini API.
```
