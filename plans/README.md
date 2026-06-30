# Plans Log Index

Single Source of Truth for planning logs.

## Entries

- [20260630_1605-vision-resume-plan.md](./20260630_1605-vision-resume-plan.md): Kế hoạch resume vision 21 JPG với nhịp tuần tự để tránh quota.
- [20260630_1115-asr-vision-sequential-plan.md](./20260630_1115-asr-vision-sequential-plan.md): ASR xong; vision JPG chờ quota; resume PDF batch sau.
- [20260630_1040-multi-format-ingest-plan.md](./20260630_1040-multi-format-ingest-plan.md): Plan thực thi ingest docx/jpg + enrich; m4a ASR pending.
- [20260630_1005-multi-format-ingest-plan.md](./20260630_1005-multi-format-ingest-plan.md): Routing docx/xlsx/ảnh → markdown; mở rộng ocr_catalog_postgres.
- [20260630_0915-dual-lane-pipeline-config-plan.md](./20260630_0915-dual-lane-pipeline-config-plan.md): Thiết kế 2 lane + enrich + toàn bộ VAR trong pipeline_config.
- [20260630_0901-vision-ai-metadata-plan.md](./20260630_0901-vision-ai-metadata-plan.md): Kế thừa metadata enrich sang Vision extraction cho Teable ai_*.
- [20260630_0851-vision-incremental-teable-plan.md](./20260630_0851-vision-incremental-teable-plan.md): Teable sync từng doc sau vision OCR; backfill + batch mới.
- [20260630_0810-vision-parallel-rollout-plan.md](./20260630_0810-vision-parallel-rollout-plan.md): Rollout vision batch 444 doc ∥ Teable loop, sleep 12s, post-sync effective.
- [20260629_1748-gemini-model-comparison-plan.md](./20260629_1748-gemini-model-comparison-plan.md): Probe 1.5-pro (fail), so sánh 4 lane extraction, giữ 2.5-flash.
- [20260629_1552-teable-live-sync-plan.md](./20260629_1552-teable-live-sync-plan.md): Kế hoạch đẩy Teable liên tục bằng loop sync 5 phút.
- [20260629_1545-google-vision-rollout-plan.md](./20260629_1545-google-vision-rollout-plan.md): Rollout Google Gemini vision (2.5 flash/pro) với nhịp chậm cho free-tier.
- [20260629_1540-gemini-codex-retry-plan.md](./20260629_1540-gemini-codex-retry-plan.md): Retry Gemini chậm/backoff rồi chạy vision batch song song.
- [20260629_1425-vision-api-unblock-plan.md](./20260629_1425-vision-api-unblock-plan.md): Chạy vision batch sau khi check_vision_api pass.
- [20260629_1416-dev-parallel-execution-plan.md](./20260629_1416-dev-parallel-execution-plan.md): DEV song song DeepSeek enrich ∥ Gemini vision + post-sync.
- [20260629_1334-dev-sequential-execution-plan.md](./20260629_1334-dev-sequential-execution-plan.md): DEV chạy lần lượt Vision → Q&A → full AI enrich.
- [20260629_1258-priority-search-vision-execution-plan.md](./20260629_1258-priority-search-vision-execution-plan.md): Thực thi P1–P3 — cache effective, search API, Celery vision.
- [20260629_1250-priority-search-vision-plan.md](./20260629_1250-priority-search-vision-plan.md): Waterfall priority, dọn OwnCloud, staff search, Celery gemini-3-flash.
- [20260629_1215-taxonomy-teable-sync-plan.md](./20260629_1215-taxonomy-teable-sync-plan.md): Quy ước taxonomy + Teable singleSelect/multipleSelect trước sync.
- [20260629_1155-multi-version-extraction-plan.md](./20260629_1155-multi-version-extraction-plan.md): Plan Webchat → Teable, priority versions, API quyền tắt sau setup.
- [20260629_1141-teable-views-plan.md](./20260629_1141-teable-views-plan.md): Views Teable + search sau khi đủ 16 cột catalog.
- [20260629_1134-teable-sync-expand-plan.md](./20260629_1134-teable-sync-expand-plan.md): Mở rộng cột Teable sau MVP sync 475 doc.
- [20260626_1803-ai-enrich-full-batch-plan.md](./20260626_1803-ai-enrich-full-batch-plan.md): Plan full AI enrich ~439 doc sau pilot 15 (~2.6h).
- [20260625_2319-concept-search-plan.md](./20260625_2319-concept-search-plan.md): Plan concept registry + multi-signal search (use case phạm vi hành nghề).
- [20260625_2313-ai-taxonomy-enrichment-plan.md](./20260625_2313-ai-taxonomy-enrichment-plan.md): Plan taxonomy AI + context API (filter structural → enrich → Q&A subset).
- [20260625_2056-ocr-full-batch-plan.md](./20260625_2056-ocr-full-batch-plan.md): Plan chạy OCR full batch `--all` đo SLA toàn bộ PDF.
- [20260625_1857-teable-integration-plan.md](./20260625_1857-teable-integration-plan.md): Plan tích hợp Teable làm UI catalog (schema bảng, env, sync script).
- [20260625_1853-ocr-sla-batch-plan.md](./20260625_1853-ocr-sla-batch-plan.md): Plan OCR batch với SLA timing và scale tiếp.
- [20260625_1840-catalog-reconcile-plan.md](./20260625_1840-catalog-reconcile-plan.md): Quy trình sync + prune sau khi xóa file trên OCIS.
- [20260625_1834-postgres-catalog-ui-plan.md](./20260625_1834-postgres-catalog-ui-plan.md): Plan UI catalog Postgres (table + detail) và mở rộng sau.
- [20260625_1829-hth-shared-drive-next-steps.md](./20260625_1829-hth-shared-drive-next-steps.md): Checklist sau sync HTH-Shared-Drive (OCR batch là bước kế).
- [20260625_1819-hung-thinh-dept-cloud-plan.md](./20260625_1819-hung-thinh-dept-cloud-plan.md): Kế hoạch triển khai Cloud theo phòng ban cho BV Hưng Thịnh.
- [20260625_1815-ocis-project-space-plan.md](./20260625_1815-ocis-project-space-plan.md): Kế hoạch tạo Project Space (Shared Drive) và chỉnh sync OCR.
- [20260625_1801-ocis-migration-checklist.md](./20260625_1801-ocis-migration-checklist.md): Checklist after switching from legacy ownCloud Server to OCIS 8.0.4.
- [20260625_1753-owncloud-postgres-pdca-plan.md](./20260625_1753-owncloud-postgres-pdca-plan.md): PDCA plan/check/act for OwnCloud sync, Postgres SoT, AI enrich, verified backfill.
- [20260625_1743-low-cost-search-architecture-plan.md](./20260625_1743-low-cost-search-architecture-plan.md): Phased plan for metadata, FTS, tags, and AI-on-subset retrieval.
- [20260625_1731-ai-api-usage-plan.md](./20260625_1731-ai-api-usage-plan.md): API group/model policy for text OCR review vs image models.
- [20260625_1705-quality-ocr-operation-plan.md](./20260625_1705-quality-ocr-operation-plan.md): Quality-first EasyOCR operational preset and run discipline.
- [20260625_1652-ocr-spa-deployment-plan.md](./20260625_1652-ocr-spa-deployment-plan.md): Run/deploy steps for OCR SQLite SPA with port pre-check.
- [20260625_1634-easyocr-as-baseline-plan.md](./20260625_1634-easyocr-as-baseline-plan.md): Adopt EasyOCR DB as current baseline and keep others for regression checks.
- [20260625_1612-next-quality-eval-plan.md](./20260625_1612-next-quality-eval-plan.md): Plan for field-level Vietnamese OCR quality benchmarking.
- [20260625_1603-vietnamese-ocr-improvement-plan.md](./20260625_1603-vietnamese-ocr-improvement-plan.md): Experiment plan to improve Vietnamese OCR quality.
- [20260625_1559-next-evaluation-step.md](./20260625_1559-next-evaluation-step.md): Follow-up plan for OCR quality comparison runs.
- [20260625_1551-production-ocr-folder-plan.md](./20260625_1551-production-ocr-folder-plan.md): Lifecycle plan for production OCR folder operations.
- [20260625_1547-mvp-usage-plan.md](./20260625_1547-mvp-usage-plan.md): Runbook for using the folder-to-SQLite MVP and OCR modes.
- [20260625_1538-ocr-to-sqlite-plan.md](./20260625_1538-ocr-to-sqlite-plan.md): Practical plan for OCR conversion and temporary SQLite storage.
- [20260625_1512-next-steps-after-fork.md](./20260625_1512-next-steps-after-fork.md): Action plan after setting up fork remotes.
- [20260625_1508-git-workflow.md](./20260625_1508-git-workflow.md): Recommended push and merge plan for current repository state.
