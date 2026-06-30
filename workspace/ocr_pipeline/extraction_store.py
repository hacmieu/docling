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


def _tags_json(tags: Any) -> str:
    if isinstance(tags, str):
        return tags
    return json.dumps(tags or [], ensure_ascii=False)


def _key_fields_json(key_fields: Any) -> str:
    if isinstance(key_fields, str):
        return key_fields
    return json.dumps(key_fields or {}, ensure_ascii=False)


def inherit_document_ai_metadata(conn: Any, document_id: int, extraction_id: int) -> bool:
    """
    Copy AI category/doc_type/tags from documents (or deepseek_cleanup fallback)
    onto a google_vision extraction so Teable ai_* columns can be filled.
    """
    existing = conn.execute(
        "SELECT category, doc_type FROM document_extractions WHERE id = %s",
        (extraction_id,),
    ).fetchone()
    if existing and (existing[0] or existing[1]):
        return False

    doc = conn.execute(
        """
        SELECT ai_category, ai_doc_type, ai_tags, ai_key_fields, ai_review
        FROM documents WHERE id = %s
        """,
        (document_id,),
    ).fetchone()
    category = doc_type = review = None
    tags: Any = []
    key_fields: Any = {}
    if doc and (doc[0] or doc[1]):
        category, doc_type, tags, key_fields, review = doc
    else:
        fallback = conn.execute(
            """
            SELECT category, doc_type, tags, key_fields, extracted_summary
            FROM document_extractions
            WHERE document_id = %s AND source_type = 'deepseek_cleanup'
            ORDER BY id DESC
            LIMIT 1
            """,
            (document_id,),
        ).fetchone()
        if fallback:
            category, doc_type, tags, key_fields, review = fallback

    if not category and not doc_type:
        return False

    conn.execute(
        """
        UPDATE document_extractions SET
            category = %s,
            doc_type = %s,
            tags = %s::jsonb,
            key_fields = %s::jsonb,
            extracted_summary = COALESCE(NULLIF(%s, ''), extracted_summary),
            version_status = 'active',
            updated_at = NOW()
        WHERE id = %s
        """,
        (
            category or "",
            doc_type or "",
            _tags_json(tags),
            _key_fields_json(key_fields),
            review or "",
            extraction_id,
        ),
    )
    return True


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
