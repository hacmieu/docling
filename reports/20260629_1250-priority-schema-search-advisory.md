# Report — Tư vấn priority, schema, search, Gemini queue

## 1. Priority: waterfall, không phải «active thì dùng»

### Hiểu đúng

Với mỗi `document_id`, hệ thống chọn **một** bản metadata theo thang ưu tiên:

```
human_verified (100) → có thì dùng
    ↓ không có
human_webchat (95)
    ↓
google_vision (70)
    ↓
deepseek_cleanup (50)
    ↓
local_llm_ocr (30)   ← luôn có nếu đã OCR
```

- Chỉ loại `archived`, `superseded` khỏi fallback.
- `draft` vẫn được chọn nếu là tier cao nhất hiện có (VD nhân viên đang sửa Webchat chưa verify).

### Đã thêm

- View SQL: `effective_document_extractions`
- Python: `resolve_effective_extraction()` trong `extraction_priority.py`

---

## 2. Field thừa trên OwnCloud?

Sau khi tách **DocExtractions**, bảng **OwnCloud** nên là **chỉ mục file**, không phải bản sao metadata AI.

| Field | Thừa? | Lý do |
|-------|--------|-------|
| **ai_category, ai_doc_type, ai_tags** | **Có** | Trùng DocExtractions; dễ lệch khi có nhiều version |
| **ai_review** | **Có** | → `extracted_summary` trên extraction |
| **_link_child_test** | **Có** | Link test, nên xóa |
| markdown_preview | Tạm giữ | Search FTS nhanh; có thể chuyển sang RAW extraction |
| active_priority, active_source | OK nếu **computed** | Cache kết quả waterfall, không sửa tay |
| ocr_*, path, phong_ban, Number | **Giữ** | Catalog + pipeline |
| DocExtractions (link) | **Giữ** | Quan hệ 1-nhiều đúng |
| Status (To do/Done) | **Giữ** | Trạng thái pipeline UI |

**Khuyến nghị:** Xóa/lookup hóa 4 field AI trên OwnCloud; sync `active_*` từ view `effective_document_extractions`.

---

## 3. Table & quan hệ — đúng chưa?

### Postgres — **đúng hướng**

| Bảng | Vai trò |
|------|---------|
| documents | File + OCR markdown gốc |
| document_extractions | Mọi version (RAW, DeepSeek, Vision, human…) |
| prompt_templates | Prompt Webchat |
| tags / document_tags | Facet (nên sync từ **effective** extraction) |

Thiếu (phase sau): `vision_jobs` hoặc Celery result backend cho hàng đợi Gemini.

### Teable — **đúng, cần dọn**

| Bảng | Quan hệ | Ghi chú |
|------|---------|---------|
| OwnCloud | hub | Giảm field AI trùng |
| DocExtractions | manyOne → OwnCloud | Đúng |
| PromptTemplates | độc lập | Đúng |

---

## 4. Nhân viên hỏi «phạm vi hành nghề» — tìm & show thế nào?

### Bước 1 — Thu hẹp (0 token LLM)

```sql
-- Concept + FTS
SELECT d.id, d.owncloud_path, e.category, e.tags, e.extracted_summary,
       left(d.markdown, 500) AS excerpt
FROM documents d
JOIN effective_document_extractions e ON e.document_id = d.id
WHERE d.owncloud_path LIKE 'project/hth-shared-drive%'
  AND (
    d.markdown ILIKE '%phạm vi hành nghề%'
    OR e.tags ? 'pham-vi-hanh-nghe'  -- sau normalize
    OR e.category ILIKE '%hành nghề%'
  );
```

### Bước 2 — Show trên Teable

- View **OwnCloud**: filter linked DocExtractions / effective lookup
- Hoặc View **DocExtractions**: filter `ai_tags` contains `pham-vi-hanh-nghe`
- Mỗi dòng: tên file, phòng ban, **nguồn đang dùng** (`active_source`), snippet

### Bước 3 — Hỏi sâu (có token)

User chọn ≤10 doc → API context gửi `effective` excerpt + `key_fields` → **DeepSeek** trả lời.

**Không** đọc 475 file; **không** dùng Gemini cho bước chat text.

---

## 5. Gemini (vision) + Celery — tránh 429

Nhà cung cấp: `gemini-3-flash` / `gemini-3-flash-thinking` **chỉ đọc ảnh**.

| Tầng | Công nghệ | Model/key |
|------|-----------|-----------|
| Text enrich / chat | Sync hoặc queue riêng | DeepSeek + `AI_BOX_API_KEY` |
| Đọc ảnh/PDF scan | **Celery worker** + rate limit | `AI_BOX_VISION_API_KEY` + `gemini-3-flash` |

Luồng:

```
Producer → Redis queue → Worker (max N/min, retry 429)
  → google_vision extraction row (priority 70)
  → normalize → Teable sync
```

ENV mẫu (`.env.example`): `AI_BOX_VISION_API_KEY`, `CELERY_BROKER_URL`, `CELERY_VISION_RATE_LIMIT`.

**Không** commit key thật vào git.

---

## Verdict

- Priority: **waterfall theo điểm**, đã có view + hàm resolve.
- OwnCloud: **có field thừa** (ai_*), nên lookup/computed.
- Schema: **đúng**; thêm Celery cho Vision là bước tiếp.
- Search staff: **concept + FTS + effective extraction** → list → optional DeepSeek.
