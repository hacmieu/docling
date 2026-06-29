# Memory Log Index

Single Source of Truth for memory logs.

## Entries

- [20260629_1545-google-vision-switch.md](./20260629_1545-google-vision-switch.md): Đã chuyển lane vision sang Google API và pilot 2/2 thành công.
- [20260629_1540-gemini-codex-check.md](./20260629_1540-gemini-codex-check.md): Gemini key có quyền model; test OCR trả 429 resource exhausted.
- [20260629_1425-vision-key-fix-and-diagnosis.md](./20260629_1425-vision-key-fix-and-diagnosis.md): Sửa trùng key vision; 503 AI Box chưa có kênh gemini-3-flash.
- [20260629_1416-dev-parallel-status-summary.md](./20260629_1416-dev-parallel-status-summary.md): Tổng kết dự án + lane song song enrich/vision.
- [20260629_1334-dev-sequential-execution.md](./20260629_1334-dev-sequential-execution.md): DEV lần lượt — Vision (block key), Q&A search, enrich pilot 5 + full batch nền.
- [20260629_1258-priority-search-vision-implementation.md](./20260629_1258-priority-search-vision-implementation.md): Triển khai cache waterfall, /api/search, Celery Gemini vision, dọn OwnCloud Teable.
- [20260629_1250-priority-waterfall-gemini-queue.md](./20260629_1250-priority-waterfall-gemini-queue.md): Priority waterfall (không chỉ active); field thừa OwnCloud; Celery Gemini vision.
- [20260629_1215-metadata-normalize-extraction-sync.md](./20260629_1215-metadata-normalize-extraction-sync.md): Chuẩn hóa category/doc_type/tags; migrate 462 DocExtractions RAW+DeepSeek.
- [20260629_1155-multi-version-extraction-flow.md](./20260629_1155-multi-version-extraction-flow.md): Flow đa phiên bản — human > Google Vision > DeepSeek > OCR local; 6 bảng Postgres.
- [20260629_1141-teable-fields-expanded.md](./20260629_1141-teable-fields-expanded.md): 13 field API mới + resync 475 row đầy đủ (path, OCR preview, AI tags).
- [20260629_1134-postgres-teable-sync.md](./20260629_1134-postgres-teable-sync.md): Postgres 4 bảng; sync 475 doc lên Teable noibo (MVP Label/Number/Status).
- [20260626_1803-ai-enrich-pilot15.md](./20260626_1803-ai-enrich-pilot15.md): Pilot AI enrich 15 doc — 15/15 OK sau retry; ~17s API/doc.
- [20260625_2319-concept-search-narrowing.md](./20260625_2319-concept-search-narrowing.md): Thu hẹp không gian tìm kiếm — ví dụ «phạm vi hành nghề»; FTS + tag + concept map trước AI.
- [20260625_2313-ai-category-tag-direction.md](./20260625_2313-ai-category-tag-direction.md): AI category/tag bổ sung API context kiểu email — không thay lớp lọc path/ngày/luồng.
- [20260625_2056-ocr-full-batch-sla.md](./20260625_2056-ocr-full-batch-sla.md): Full OCR 437 PDF (~78 phút); Teable ENV placeholder trong .env.
- [20260625_1857-teable-ui-instead-of-fe.md](./20260625_1857-teable-ui-instead-of-fe.md): Teable thay custom FE — sync Postgres→Teable API, không mount DB trực tiếp.
- [20260625_1853-ocr-batch10-sla.md](./20260625_1853-ocr-batch10-sla.md): Pilot OCR 10 PDF từ OCIS → Postgres với đo SLA.
- [20260625_1840-catalog-prune-vietnamese-ui.md](./20260625_1840-catalog-prune-vietnamese-ui.md): Prune/dedupe catalog; sửa font tiếng Việt trên webapp Postgres.
- [20260625_1834-postgres-catalog-webapp.md](./20260625_1834-postgres-catalog-webapp.md): Webapp PostgreSQL table list + detail trên port 8766.
- [20260625_1829-hth-shared-drive-synced.md](./20260625_1829-hth-shared-drive-synced.md): Project Space HTH-Shared-Drive sync 491 file vào Postgres catalog.
- [20260625_1819-hung-thinh-hospital-context.md](./20260625_1819-hung-thinh-hospital-context.md): Bối cảnh BV Hưng Thịnh — cloud phòng ban cho AI và collaboration.
- [20260625_1815-ocis-shared-drive-spaces.md](./20260625_1815-ocis-shared-drive-spaces.md): OCIS Project Spaces tương đương Google Shared Drive / SharePoint; khuyến nghị dùng cho OCR team.
- [20260625_1801-owncloud-ocis-not-nextcloud.md](./20260625_1801-owncloud-ocis-not-nextcloud.md): Clarified ownCloud vs Nextcloud; migrated infra target to OCIS 8.0.4.
- [20260625_1753-owncloud-postgres-rollout.md](./20260625_1753-owncloud-postgres-rollout.md): OwnCloud local + PostgreSQL SoT rollout with AI metadata enrichment design.
- [20260625_1743-architecture-direction-discussion.md](./20260625_1743-architecture-direction-discussion.md): Advisory on metadata-first catalog with Nextcloud and low-cost AI usage.
- [20260625_1731-ai-review-deepseek-default-group.md](./20260625_1731-ai-review-deepseek-default-group.md): AI review columns, DeepSeek default-group model, 23/23 success.
- [20260625_1705-light-theme-and-quality-rerun.md](./20260625_1705-light-theme-and-quality-rerun.md): Light-theme SPA plus quality-first EasyOCR rerun and active DB update.
- [20260625_1652-ocr-spa-webapp.md](./20260625_1652-ocr-spa-webapp.md): Lightweight SPA webapp created for browsing OCR SQLite data.
- [20260625_1634-active-db-easyocr.md](./20260625_1634-active-db-easyocr.md): Set EasyOCR output as active OCR evaluation DB.
- [20260625_1612-vietnamese-ocr-comparison-runs.md](./20260625_1612-vietnamese-ocr-comparison-runs.md): Executed three Vietnamese OCR configurations for comparison.
- [20260625_1603-vietnamese-ocr-options.md](./20260625_1603-vietnamese-ocr-options.md): Added Vietnamese-focused OCR engine and language tuning options.
- [20260625_1559-ingestion-run-completed.md](./20260625_1559-ingestion-run-completed.md): First OCR ingestion run completed into SQLite with 13/13 success.
- [20260625_1551-ocr-workspace-structure.md](./20260625_1551-ocr-workspace-structure.md): Production-oriented OCR workspace scaffolding.
- [20260625_1547-mvp-folder-to-sqlite.md](./20260625_1547-mvp-folder-to-sqlite.md): MVP script creation for folder ingestion into SQLite.
- [20260625_1538-ocr-sqlite-direction.md](./20260625_1538-ocr-sqlite-direction.md): Direction check for OCR to temporary SQLite memory.
- [20260625_1512-fork-remote-setup.md](./20260625_1512-fork-remote-setup.md): Remotes switched to fork workflow (`origin` and `upstream`).
- [20260625_1508-git-workflow.md](./20260625_1508-git-workflow.md): Current branch/push target and merge flow guidance.
