#!/usr/bin/env python3
"""Normalize ai_category, ai_doc_type, ai_tags in Postgres catalog + extractions."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workspace.ocr_pipeline.db_postgres import connect, load_dotenv
from workspace.ocr_pipeline.metadata_normalize import (
    normalize_category,
    normalize_doc_type,
    normalize_tags,
)

MIGRATION = (
    REPO_ROOT / "workspace/ocr_pipeline/infra/postgres/migrations/003_extraction_doc_type.sql"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_dotenv()
    docs_updated = extractions_updated = 0

    with connect() as conn:
        if not args.dry_run:
            conn.execute(MIGRATION.read_text(encoding="utf-8"))

        doc_rows = conn.execute(
            """
            SELECT id, ai_category, ai_doc_type, ai_tags
            FROM documents
            WHERE ai_category IS NOT NULL OR ai_doc_type IS NOT NULL OR ai_tags != '[]'::jsonb
            """
        ).fetchall()

        for doc_id, category, doc_type, tags in doc_rows:
            cat_slug, cat_label = normalize_category(category)
            type_slug, _type_label = normalize_doc_type(doc_type)
            norm_tags = normalize_tags(tags)
            if args.dry_run:
                docs_updated += 1
                continue
            conn.execute(
                """
                UPDATE documents SET
                    ai_category = %s,
                    ai_doc_type = %s,
                    ai_tags = %s::jsonb,
                    updated_at = NOW()
                WHERE id = %s
                """,
                (cat_label, type_slug, json.dumps(norm_tags, ensure_ascii=False), doc_id),
            )
            docs_updated += 1

        ext_rows = conn.execute(
            """
            SELECT e.id, e.category, e.tags, e.doc_type, d.ai_doc_type
            FROM document_extractions e
            JOIN documents d ON d.id = e.document_id
            """
        ).fetchall()

        for ext_id, category, tags, ext_doc_type, doc_ai_type in ext_rows:
            source_row = conn.execute(
                "SELECT source_type FROM document_extractions WHERE id = %s", (ext_id,)
            ).fetchone()
            source_type = source_row[0] if source_row else ""
            if source_type == "local_llm_ocr":
                cat_label = None
                type_slug = None
                norm_tags = []
            else:
                _cat_slug, cat_label = normalize_category(category)
                type_slug, _ = normalize_doc_type(ext_doc_type or doc_ai_type)
                norm_tags = normalize_tags(tags)
            if args.dry_run:
                extractions_updated += 1
                continue
            conn.execute(
                """
                UPDATE document_extractions SET
                    category = %s,
                    doc_type = %s,
                    tags = %s::jsonb,
                    updated_at = NOW()
                WHERE id = %s
                """,
                (cat_label, type_slug, json.dumps(norm_tags, ensure_ascii=False), ext_id),
            )
            extractions_updated += 1

        # Backfill doc_type on deepseek rows from documents if still null
        if not args.dry_run:
            conn.execute(
                """
                UPDATE document_extractions e SET
                    doc_type = d.ai_doc_type,
                    category = COALESCE(e.category, d.ai_category),
                    tags = CASE
                        WHEN e.tags = '[]'::jsonb AND d.ai_tags != '[]'::jsonb THEN d.ai_tags
                        ELSE e.tags
                    END,
                    updated_at = NOW()
                FROM documents d
                WHERE d.id = e.document_id
                  AND e.source_type = 'deepseek_cleanup'
                  AND (e.doc_type IS NULL OR e.doc_type = '')
                """
            )

    print(
        f"Normalized documents={docs_updated} extractions={extractions_updated} "
        f"{'(dry-run)' if args.dry_run else ''}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
