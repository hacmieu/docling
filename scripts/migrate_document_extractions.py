#!/usr/bin/env python3
"""Apply Postgres migrations and backfill extraction versions from existing AI/OCR data."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workspace.ocr_pipeline.db_postgres import connect, load_dotenv
from workspace.ocr_pipeline.extraction_priority import SOURCE_PRIORITY

MIGRATION = (
    REPO_ROOT / "workspace/ocr_pipeline/infra/postgres/migrations/002_document_extractions.sql"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def apply_migration(conn) -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    conn.execute(sql)


def next_version_no(conn, document_id: int) -> int:
    row = conn.execute(
        "SELECT COALESCE(MAX(version_no), 0) + 1 FROM document_extractions WHERE document_id = %s",
        (document_id,),
    ).fetchone()
    return int(row[0])


def backfill_local_ocr(conn, dry_run: bool) -> int:
    rows = conn.execute(
        """
        SELECT id, markdown, status
        FROM documents
        WHERE status = 'success' AND length(coalesce(markdown, '')) > 0
        """
    ).fetchall()
    count = 0
    for doc_id, markdown, status in rows:
        exists = conn.execute(
            """
            SELECT 1 FROM document_extractions
            WHERE document_id = %s AND source_type = 'local_llm_ocr'
            """,
            (doc_id,),
        ).fetchone()
        if exists:
            continue
        version_no = next_version_no(conn, doc_id)
        if dry_run:
            count += 1
            continue
        conn.execute(
            """
            INSERT INTO document_extractions (
                document_id, version_no, source_type, priority_score, version_status,
                raw_text, extracted_summary, model_name, created_by
            ) VALUES (%s, %s, 'local_llm_ocr', %s, 'active', %s, %s, %s, %s)
            """,
            (
                doc_id,
                version_no,
                SOURCE_PRIORITY["local_llm_ocr"],
                markdown,
                "OCR markdown (EasyOCR pipeline)",
                "docling-easyocr",
                "system:ocr_pipeline",
            ),
        )
        count += 1
    return count


def backfill_deepseek(conn, dry_run: bool) -> int:
    rows = conn.execute(
        """
        SELECT id, ai_category, ai_tags, ai_key_fields, ai_review, ai_review_model, ai_review_status
        FROM documents
        WHERE ai_review_status = 'success'
        """
    ).fetchall()
    count = 0
    for doc_id, category, tags, key_fields, summary, model, review_status in rows:
        exists = conn.execute(
            """
            SELECT 1 FROM document_extractions
            WHERE document_id = %s AND source_type = 'deepseek_cleanup'
            """,
            (doc_id,),
        ).fetchone()
        if exists:
            continue
        version_no = next_version_no(conn, doc_id)
        if dry_run:
            count += 1
            continue
        conn.execute(
            """
            INSERT INTO document_extractions (
                document_id, version_no, source_type, priority_score, version_status,
                category, tags, key_fields, extracted_summary, model_name, created_by
            ) VALUES (%s, %s, 'deepseek_cleanup', %s, 'active', %s, %s::jsonb, %s::jsonb, %s, %s, %s)
            """,
            (
                doc_id,
                version_no,
                SOURCE_PRIORITY["deepseek_cleanup"],
                category,
                json.dumps(tags or [], ensure_ascii=False),
                json.dumps(key_fields or {}, ensure_ascii=False),
                summary,
                model or "deepseek",
                "system:ai_enrich",
            ),
        )
        count += 1
    return count


def main() -> int:
    args = parse_args()
    load_dotenv()
    with connect() as conn:
        if not args.dry_run:
            apply_migration(conn)
        ocr_rows = backfill_local_ocr(conn, args.dry_run)
        ai_rows = backfill_deepseek(conn, args.dry_run)
    print(
        f"Migration {'(dry-run) ' if args.dry_run else ''}done. "
        f"local_llm_ocr inserted={ocr_rows} deepseek_cleanup inserted={ai_rows}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
