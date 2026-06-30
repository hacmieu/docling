#!/usr/bin/env python3
"""Backfill AI metadata on google_vision extractions and re-push to Teable."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workspace.ocr_pipeline.db_postgres import connect, load_dotenv
from workspace.ocr_pipeline.extraction_store import inherit_document_ai_metadata
from workspace.ocr_pipeline.teable_incremental_sync import TeableSyncContext, sync_extraction_and_document


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resync-teable", action="store_true", default=True)
    parser.add_argument("--no-resync-teable", action="store_false", dest="resync_teable")
    args = parser.parse_args()

    with connect() as conn:
        rows = conn.execute(
            """
            SELECT document_id, id FROM document_extractions
            WHERE source_type = 'google_vision'
              AND (category IS NULL OR category = '')
            ORDER BY id
            """
        ).fetchall()

    inherited = 0
    with connect() as conn:
        for doc_id, ext_id in rows:
            if inherit_document_ai_metadata(conn, int(doc_id), int(ext_id)):
                inherited += 1
                print(f"[INHERIT] doc_id={doc_id} ext_id={ext_id}")

    print(f"Inherited metadata for {inherited} extraction(s)")

    if not args.resync_teable:
        return 0

    with connect() as conn:
        all_rows = conn.execute(
            "SELECT document_id, id FROM document_extractions WHERE source_type = 'google_vision' ORDER BY id"
        ).fetchall()
    ctx = TeableSyncContext.load()
    ok = fail = 0
    for doc_id, ext_id in all_rows:
        result = sync_extraction_and_document(ctx, int(doc_id), int(ext_id))
        if result.get("error"):
            fail += 1
            print(f"[TEABLE-FAIL] doc_id={doc_id} {result['error']}")
        else:
            ok += 1
    print(f"Teable resync: ok={ok} fail={fail}")
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
