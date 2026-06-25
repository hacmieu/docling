#!/usr/bin/env python3
"""Import backdated verified metadata and attach to documents."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workspace.ocr_pipeline.db_postgres import connect, link_document_tags, load_dotenv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-json",
        type=Path,
        required=True,
        help="JSON array file: [{owncloud_path|source_path, verified_metadata, verified_at, verified_source, tags?, category?}]",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_dotenv()
    payload = json.loads(args.input_json.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        print("Input must be a JSON array")
        return 1

    updated = 0
    with connect() as conn:
        for item in payload:
            path = item.get("owncloud_path") or item.get("source_path")
            if not path:
                continue
            verified_at = item.get("verified_at")
            verified_source = item.get("verified_source", "legacy")
            verified_metadata = item.get("verified_metadata", {})
            category = item.get("category")
            tags = item.get("tags", [])

            row = conn.execute(
                """
                UPDATE documents SET
                    verified_metadata = %s::jsonb,
                    verified_at = %s,
                    verified_source = %s,
                    ai_category = COALESCE(%s, ai_category),
                    updated_at = NOW()
                WHERE owncloud_path = %s OR source_path = %s OR local_path = %s
                RETURNING id
                """,
                (
                    json.dumps(verified_metadata, ensure_ascii=False),
                    verified_at,
                    verified_source,
                    category,
                    path,
                    path,
                    path,
                ),
            ).fetchone()
            if not row:
                print(f"[MISS] {path}")
                continue
            doc_id = int(row[0])
            if tags:
                link_document_tags(conn, doc_id, [str(t) for t in tags])
            updated += 1
            print(f"[OK] id={doc_id} path={path}")

    print(f"Imported verified metadata for {updated} documents.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
