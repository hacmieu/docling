#!/usr/bin/env python3
"""DEV: run Gemini vision OCR synchronously (no Celery worker)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workspace.ocr_pipeline.db_postgres import connect, load_dotenv
from workspace.ocr_pipeline.tasks.vision_tasks import vision_ocr_document


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--doc-id", type=int, required=True)
    parser.add_argument("--dry-run", action="store_true", help="Only validate local file exists.")
    return parser.parse_args()


def main() -> int:
    load_dotenv()
    args = parse_args()
    with connect() as conn:
        row = conn.execute(
            "SELECT id, local_path, owncloud_path FROM documents WHERE id = %s",
            (args.doc_id,),
        ).fetchone()
    if not row:
        print(f"Document {args.doc_id} not found")
        return 1
    doc_id, local_path, owncloud_path = row
    print(f"doc_id={doc_id} path={owncloud_path}")
    if args.dry_run:
        path = Path(local_path or "")
        print(f"local_path exists={path.is_file()} -> {local_path}")
        return 0 if path.is_file() else 2

    result = vision_ocr_document(args.doc_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
