#!/usr/bin/env python3
"""Export side-by-side comparison of extraction versions for sample documents."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workspace.ocr_pipeline.db_postgres import connect

SOURCE_TYPES = ("local_llm_ocr", "deepseek_cleanup", "google_vision")


def fetch_comparison(document_ids: list[int], excerpt_len: int = 500) -> list[dict]:
    rows: list[dict] = []
    with connect() as conn:
        for doc_id in document_ids:
            doc = conn.execute(
                """
                SELECT id, owncloud_path, effective_source_type, effective_priority
                FROM documents WHERE id = %s
                """,
                (doc_id,),
            ).fetchone()
            if not doc:
                continue
            entry: dict = {
                "document_id": doc[0],
                "owncloud_path": doc[1],
                "effective": {"source": doc[2], "priority": doc[3]},
                "versions": {},
            }
            for source_type in SOURCE_TYPES:
                ext = conn.execute(
                    f"""
                    SELECT source_type, model_name, priority_score,
                           length(coalesce(raw_text, '')) AS raw_len,
                           length(coalesce(extracted_summary, '')) AS sum_len,
                           left(coalesce(nullif(raw_text, ''), extracted_summary, ''), %s)
                    FROM document_extractions
                    WHERE document_id = %s AND source_type = %s
                    ORDER BY version_no DESC
                    LIMIT 1
                    """,
                    (excerpt_len, doc_id, source_type),
                ).fetchone()
                if ext:
                    entry["versions"][source_type] = {
                        "model": ext[1],
                        "priority": ext[2],
                        "raw_len": ext[3],
                        "summary_len": ext[4],
                        "excerpt": ext[5],
                    }
            rows.append(entry)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ids",
        type=int,
        nargs="+",
        default=[503, 504, 505],
        help="Document IDs to compare",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Write JSON to this path (default: stdout)",
    )
    parser.add_argument("--excerpt-len", type=int, default=500)
    args = parser.parse_args()
    data = fetch_comparison(args.ids, excerpt_len=args.excerpt_len)
    text = json.dumps(data, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(f"wrote {args.output}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
