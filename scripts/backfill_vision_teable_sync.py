#!/usr/bin/env python3
"""Backfill Teable for google_vision extractions not yet synced."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workspace.ocr_pipeline.db_postgres import connect, load_dotenv
from workspace.ocr_pipeline.teable_incremental_sync import TeableSyncContext, sync_extraction_and_document


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true", help="Sync all google_vision rows")
    args = parser.parse_args()
    clause = "" if args.all else "AND (teable_record_id IS NULL OR teable_record_id = '')"
    with connect() as conn:
        rows = conn.execute(
            f"""
            SELECT document_id, id FROM document_extractions
            WHERE source_type = 'google_vision' {clause}
            ORDER BY id
            """
        ).fetchall()
    if not rows:
        print("Nothing to backfill.")
        return 0
    ctx = TeableSyncContext.load()
    ok = fail = 0
    for doc_id, ext_id in rows:
        result = sync_extraction_and_document(ctx, int(doc_id), int(ext_id))
        if result.get("error"):
            fail += 1
            print(f"[FAIL] doc_id={doc_id} ext_id={ext_id} {result['error']}")
        else:
            ok += 1
            print(f"[OK] doc_id={doc_id} ext_id={ext_id} owncloud={result.get('owncloud_patched')}")
    print(f"Backfill end: ok={ok} fail={fail}")
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
