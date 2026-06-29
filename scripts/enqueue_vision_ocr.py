#!/usr/bin/env python3
"""Enqueue Gemini vision OCR jobs for catalog documents."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workspace.ocr_pipeline.db_postgres import connect, load_dotenv
from workspace.ocr_pipeline.tasks.vision_tasks import vision_ocr_document


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--doc-id", type=int, action="append", default=[])
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument(
        "--drive-prefix",
        default="project/hth-shared-drive",
        help="Enqueue docs with local_path under this owncloud prefix.",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def select_doc_ids(doc_ids: list[int], drive_prefix: str, limit: int) -> list[int]:
    if doc_ids:
        return doc_ids
    sql = """
        SELECT id FROM documents
        WHERE owncloud_path LIKE %s
          AND local_path IS NOT NULL AND local_path != ''
          AND status = 'success'
        ORDER BY id
    """
    params: list[object] = [f"{drive_prefix}%"]
    if limit > 0:
        sql += " LIMIT %s"
        params.append(limit)
    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [int(r[0]) for r in rows]


def main() -> int:
    load_dotenv()
    args = parse_args()
    ids = select_doc_ids(args.doc_id, args.drive_prefix, args.limit)
    if not ids:
        print("No documents to enqueue.")
        return 0
    for doc_id in ids:
        if args.dry_run:
            print(f"[DRY] enqueue vision_ocr_document doc_id={doc_id}")
            continue
        result = vision_ocr_document.delay(doc_id)
        print(f"[QUEUE] doc_id={doc_id} task_id={result.id}")
    print(f"Enqueued {len(ids)} job(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
