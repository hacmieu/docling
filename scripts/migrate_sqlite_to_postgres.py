#!/usr/bin/env python3
"""Migrate OCR SQLite catalog into PostgreSQL."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workspace.ocr_pipeline.db_postgres import connect, link_document_tags, load_dotenv

ACTIVE_DB_POINTER = REPO_ROOT / "workspace/ocr_pipeline/08_sqlite/ACTIVE_DB.txt"
DEFAULT_SQLITE = (
    REPO_ROOT / "workspace/ocr_pipeline/08_sqlite/memory_tmp_vie_easyocr_quality.db"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sqlite-db", type=Path, default=None)
    return parser.parse_args()


def resolve_sqlite(path: Path | None) -> Path:
    if path is not None:
        return path.resolve()
    if ACTIVE_DB_POINTER.exists():
        selected = ACTIVE_DB_POINTER.read_text(encoding="utf-8").strip()
        if selected:
            return (ACTIVE_DB_POINTER.parent / selected).resolve()
    return DEFAULT_SQLITE.resolve()


def parse_ai_tags(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return [str(x) for x in data]
    except json.JSONDecodeError:
        pass
    return []


def main() -> int:
    args = parse_args()
    sqlite_path = resolve_sqlite(args.sqlite_db)
    if not sqlite_path.exists():
        print(f"SQLite DB not found: {sqlite_path}")
        return 1

    load_dotenv()
    conn_sqlite = sqlite3.connect(sqlite_path)
    conn_sqlite.row_factory = sqlite3.Row
    rows = conn_sqlite.execute("SELECT * FROM documents ORDER BY id").fetchall()
    conn_sqlite.close()

    migrated = 0
    with connect() as conn:
        for row in rows:
            source_path = row["source_path"]
            owncloud_path = source_path
            doc_json_raw = row["doc_json"] or "{}"
            try:
                doc_json = json.loads(doc_json_raw)
            except json.JSONDecodeError:
                doc_json = {"raw": doc_json_raw}

            key_fields: dict[str, object] = {}
            ai_tags: list[str] = []
            if "ai_key_fields" in row.keys() and row["ai_key_fields"]:
                try:
                    key_fields = json.loads(row["ai_key_fields"])
                except json.JSONDecodeError:
                    key_fields = {}
            if "ai_tags" in row.keys():
                ai_tags = parse_ai_tags(row["ai_tags"])

            inserted = conn.execute(
                """
                INSERT INTO documents (
                    owncloud_path, local_path, source_path, source_sha256,
                    markdown, doc_json, status, error_message,
                    ai_review, ai_review_status, ai_review_at, ai_review_model, ai_review_error,
                    ai_doc_type, ai_category, ai_tags, ai_key_fields, ai_ocr_quality,
                    verified_metadata, verified_at, verified_source,
                    created_at, updated_at
                )
                VALUES (
                    %s, %s, %s, %s,
                    %s, %s::jsonb, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s::jsonb, %s::jsonb, %s,
                    %s::jsonb, %s, %s,
                    %s, %s
                )
                ON CONFLICT (owncloud_path) DO UPDATE SET
                    local_path = EXCLUDED.local_path,
                    source_path = EXCLUDED.source_path,
                    source_sha256 = EXCLUDED.source_sha256,
                    markdown = EXCLUDED.markdown,
                    doc_json = EXCLUDED.doc_json,
                    status = EXCLUDED.status,
                    error_message = EXCLUDED.error_message,
                    ai_review = EXCLUDED.ai_review,
                    ai_review_status = EXCLUDED.ai_review_status,
                    ai_review_at = EXCLUDED.ai_review_at,
                    ai_review_model = EXCLUDED.ai_review_model,
                    ai_review_error = EXCLUDED.ai_review_error,
                    ai_doc_type = EXCLUDED.ai_doc_type,
                    ai_category = EXCLUDED.ai_category,
                    ai_tags = EXCLUDED.ai_tags,
                    ai_key_fields = EXCLUDED.ai_key_fields,
                    ai_ocr_quality = EXCLUDED.ai_ocr_quality,
                    verified_metadata = EXCLUDED.verified_metadata,
                    verified_at = EXCLUDED.verified_at,
                    verified_source = EXCLUDED.verified_source,
                    updated_at = EXCLUDED.updated_at
                RETURNING id
                """,
                (
                    owncloud_path,
                    source_path,
                    source_path,
                    row["source_sha256"],
                    row["markdown"] or "",
                    json.dumps(doc_json, ensure_ascii=False),
                    row["status"],
                    row["error_message"],
                    row["ai_review"] if "ai_review" in row.keys() else None,
                    row["ai_review_status"] if "ai_review_status" in row.keys() else None,
                    row["ai_review_at"] if "ai_review_at" in row.keys() else None,
                    row["ai_review_model"] if "ai_review_model" in row.keys() else None,
                    row["ai_review_error"] if "ai_review_error" in row.keys() else None,
                    row["ai_doc_type"] if "ai_doc_type" in row.keys() else None,
                    row["ai_category"] if "ai_category" in row.keys() else None,
                    json.dumps(ai_tags, ensure_ascii=False),
                    json.dumps(key_fields, ensure_ascii=False),
                    row["ai_ocr_quality"] if "ai_ocr_quality" in row.keys() else None,
                    json.dumps({}, ensure_ascii=False),
                    None,
                    None,
                    row["created_at"],
                    row["updated_at"],
                ),
            ).fetchone()
            doc_id = int(inserted[0])
            if ai_tags:
                link_document_tags(conn, doc_id, ai_tags)
            migrated += 1

    print(f"Migrated {migrated} documents from {sqlite_path} to PostgreSQL.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
