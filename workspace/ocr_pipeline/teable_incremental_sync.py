"""Incremental Teable sync after each vision OCR (or single extraction)."""

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.sync_extractions_to_teable import (  # noqa: E402
    build_fields,
    fetch_allowed_select_choices,
    fetch_doc_record_map,
    fetch_extraction_record_map,
    teable_env,
    upsert_record,
)
from workspace.ocr_pipeline.db_postgres import connect, load_dotenv
from workspace.ocr_pipeline.pipeline_config import load_pipeline_config
from workspace.ocr_pipeline.extraction_store import inherit_document_ai_metadata
from workspace.ocr_pipeline.ai_enrich import enrich_extraction_from_ocr_text
from workspace.ocr_pipeline.teable_catalog import teable_config, teable_headers

MIGRATION_005 = (
    REPO_ROOT / "workspace/ocr_pipeline/infra/postgres/migrations/005_documents_effective_cache.sql"
)


@dataclass
class TeableSyncContext:
    """Cached Teable maps for fast per-document updates during long vision batches."""

    ext_cfg: dict[str, str]
    doc_cfg: dict[str, str]
    doc_map: dict[int, str]
    ext_map: dict[int, str]
    allowed_choices: dict[str, set[str]] = field(default_factory=dict)

    @classmethod
    def load(cls) -> TeableSyncContext:
        load_dotenv()
        ext_cfg = teable_env()
        doc_cfg = teable_config()
        return cls(
            ext_cfg=ext_cfg,
            doc_cfg=doc_cfg,
            doc_map=fetch_doc_record_map(ext_cfg),
            ext_map=fetch_extraction_record_map(ext_cfg),
            allowed_choices=fetch_allowed_select_choices(ext_cfg),
        )


def _ensure_effective_migration(conn: Any) -> None:
    if MIGRATION_005.exists():
        conn.execute(MIGRATION_005.read_text(encoding="utf-8"))


def recompute_effective_for_document(conn: Any, document_id: int) -> tuple[str | None, int | None, int]:
    """Update effective_* cache on one document; return (source_type, priority, version_count)."""
    _ensure_effective_migration(conn)
    conn.execute(
        """
        UPDATE documents d
        SET
            effective_extraction_id = e.extraction_id,
            effective_source_type = e.source_type,
            effective_priority = e.priority_score
        FROM effective_document_extractions e
        WHERE d.id = e.document_id AND d.id = %s
        """,
        (document_id,),
    )
    row = conn.execute(
        """
        SELECT effective_source_type, effective_priority
        FROM documents WHERE id = %s
        """,
        (document_id,),
    ).fetchone()
    version_row = conn.execute(
        "SELECT COUNT(*) FROM document_extractions WHERE document_id = %s",
        (document_id,),
    ).fetchone()
    version_count = int(version_row[0]) if version_row else 0
    if not row:
        return None, None, version_count
    return row[0], row[1], version_count


def _fetch_extraction_row(extraction_id: int) -> tuple[Any, ...] | None:
    sql = """
        SELECT
            e.id, e.document_id, e.version_no, e.source_type, e.priority_score,
            e.version_status, e.category, e.doc_type, e.tags, e.key_fields,
            e.extracted_summary, e.raw_text, e.model_name, e.created_by, e.created_at
        FROM document_extractions e
        WHERE e.id = %s
    """
    with connect() as conn:
        return conn.execute(sql, (extraction_id,)).fetchone()


def ensure_vision_extraction_enriched(
    conn: Any,
    document_id: int,
    extraction_id: int,
) -> str | None:
    """Enrich vision row if ai_* empty; returns status token or None if already filled."""
    row = conn.execute(
        "SELECT category, raw_text, source_type FROM document_extractions WHERE id = %s",
        (extraction_id,),
    ).fetchone()
    if not row:
        return None
    category, raw_text, source_type = row
    config = load_pipeline_config()
    if source_type not in {config.source_vision, "google_vision", "ai_vision"}:
        return None
    if category:
        return None
    if not config.vision_enrich_enabled:
        if config.vision_enrich_fallback_inherit:
            inherit_document_ai_metadata(conn, document_id, extraction_id)
            return "inherit_fallback"
        return None
    doc = conn.execute(
        "SELECT owncloud_path, source_path FROM documents WHERE id = %s",
        (document_id,),
    ).fetchone()
    filename = Path((doc[0] if doc else None) or (doc[1] if doc else None) or "unknown").name

    try:
        enrich_extraction_from_ocr_text(
            conn, extraction_id, raw_text or "", filename, "vision", config
        )
        return "enriched"
    except Exception:
        if config.vision_enrich_fallback_inherit:
            inherit_document_ai_metadata(conn, document_id, extraction_id)
            return "inherit_fallback"
        raise


def _patch_owncloud_row(
    ctx: TeableSyncContext,
    document_id: int,
    source_type: str | None,
    priority: int | None,
    version_count: int,
) -> bool:
    record_id = ctx.doc_map.get(document_id)
    if not record_id:
        return False
    fields: dict[str, Any] = {"extraction_version_count": version_count}
    if priority is not None:
        fields["active_priority"] = int(priority)
    if source_type:
        fields["active_source"] = source_type
    endpoint = f"{ctx.doc_cfg['url']}/table/{ctx.doc_cfg['table_id']}/record/{record_id}"
    body = {"fieldKeyType": "name", "record": {"fields": fields}}
    response = requests.patch(
        endpoint,
        headers=teable_headers(ctx.doc_cfg["token"]),
        json=body,
        timeout=60,
    )
    response.raise_for_status()
    return True


def sync_extraction_and_document(
    ctx: TeableSyncContext,
    document_id: int,
    extraction_id: int,
    *,
    sleep_seconds: float = 0.05,
) -> dict[str, Any]:
    """
    After one vision OCR: recompute effective, upsert DocExtractions, PATCH OwnCloud row.
    Returns a small result dict for logging.
    """
    result: dict[str, Any] = {
        "document_id": document_id,
        "extraction_id": extraction_id,
        "extraction_synced": False,
        "owncloud_patched": False,
        "error": None,
    }
    row = _fetch_extraction_row(extraction_id)
    if not row:
        result["error"] = "extraction not found"
        return result

    doc_record = ctx.doc_map.get(document_id)
    if not doc_record:
        result["error"] = "missing Teable OwnCloud link for doc"
        return result

    try:
        with connect() as conn:
            enrich_status = ensure_vision_extraction_enriched(conn, document_id, extraction_id)
            if enrich_status:
                result["enrich_status"] = enrich_status
        row = _fetch_extraction_row(extraction_id)
        if not row:
            result["error"] = "extraction not found after inherit"
            return result
        fields = build_fields(row, doc_record, ctx.allowed_choices)
        record_id = ctx.ext_map.get(extraction_id)
        teable_id = upsert_record(ctx.ext_cfg, fields, record_id, dry_run=False)
        with connect() as conn:
            conn.execute(
                "UPDATE document_extractions SET teable_record_id = %s WHERE id = %s",
                (teable_id, extraction_id),
            )
            source_type, priority, version_count = recompute_effective_for_document(
                conn, document_id
            )
        ctx.ext_map[extraction_id] = teable_id
        result["extraction_synced"] = True
        result["teable_extraction_id"] = teable_id
        result["created"] = record_id is None

        if sleep_seconds > 0:
            time.sleep(sleep_seconds)

        result["owncloud_patched"] = _patch_owncloud_row(
            ctx, document_id, source_type, priority, version_count
        )
    except Exception as exc:
        result["error"] = str(exc)
    return result
