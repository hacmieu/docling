"""Persist extraction rows from pipeline scripts."""

from __future__ import annotations

import json
from typing import Any

from workspace.ocr_pipeline.extraction_priority import SOURCE_PRIORITY


def next_version_no(conn: Any, document_id: int) -> int:
    row = conn.execute(
        "SELECT COALESCE(MAX(version_no), 0) + 1 FROM document_extractions WHERE document_id = %s",
        (document_id,),
    ).fetchone()
    return int(row[0])


def upsert_deepseek_extraction(
    conn: Any,
    document_id: int,
    *,
    category: str,
    doc_type: str,
    tags: list[str],
    key_fields: dict[str, object],
    summary: str,
    model_name: str,
) -> int:
    """Insert or refresh deepseek_cleanup row for a document."""
    from workspace.ocr_pipeline.metadata_normalize import (
        normalize_category,
        normalize_doc_type,
        normalize_tags,
    )

    cat_slug, cat_label = normalize_category(category)
    type_slug, _ = normalize_doc_type(doc_type)
    norm_tags = normalize_tags(tags)
    existing = conn.execute(
        """
        SELECT id FROM document_extractions
        WHERE document_id = %s AND source_type = 'deepseek_cleanup'
        ORDER BY id DESC LIMIT 1
        """,
        (document_id,),
    ).fetchone()
    if existing:
        extraction_id = int(existing[0])
        conn.execute(
            """
            UPDATE document_extractions SET
                category = %s,
                doc_type = %s,
                tags = %s::jsonb,
                key_fields = %s::jsonb,
                extracted_summary = %s,
                model_name = %s,
                version_status = 'active',
                updated_at = NOW()
            WHERE id = %s
            """,
            (
                cat_label or category,
                type_slug or doc_type,
                json.dumps(norm_tags, ensure_ascii=False),
                json.dumps(key_fields, ensure_ascii=False),
                summary,
                model_name,
                extraction_id,
            ),
        )
        return extraction_id

    version_no = next_version_no(conn, document_id)
    row = conn.execute(
        """
        INSERT INTO document_extractions (
            document_id, version_no, source_type, priority_score, version_status,
            category, doc_type, tags, key_fields, extracted_summary, model_name, created_by
        ) VALUES (%s, %s, 'deepseek_cleanup', %s, 'active', %s, %s, %s::jsonb, %s::jsonb, %s, %s, %s)
        RETURNING id
        """,
        (
            document_id,
            version_no,
            SOURCE_PRIORITY["deepseek_cleanup"],
            cat_label or category,
            type_slug or doc_type,
            json.dumps(norm_tags, ensure_ascii=False),
            json.dumps(key_fields, ensure_ascii=False),
            summary,
            model_name,
            "system:ai_enrich",
        ),
    ).fetchone()
    return int(row[0])
