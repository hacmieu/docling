#!/usr/bin/env python3
"""Re-run AI enrich on google_vision extractions (lane 2) and resync Teable."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workspace.ocr_pipeline.ai_enrich import enrich_extraction_from_ocr_text
from workspace.ocr_pipeline.db_postgres import connect, load_dotenv
from workspace.ocr_pipeline.pipeline_config import load_pipeline_config
from workspace.ocr_pipeline.teable_incremental_sync import TeableSyncContext, sync_extraction_and_document


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-enrich all vision rows (not only missing category)",
    )
    parser.add_argument("--resync-teable", action="store_true", default=True)
    parser.add_argument("--no-resync-teable", action="store_false", dest="resync_teable")
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=30.0,
        help="Pause between enrich calls (Google free-tier pacing).",
    )
    args = parser.parse_args()

    clause = "" if args.force else "AND (category IS NULL OR category = '')"
    with connect() as conn:
        rows = conn.execute(
            f"""
            SELECT e.document_id, e.id, e.raw_text, d.owncloud_path, d.source_path
            FROM document_extractions e
            JOIN documents d ON d.id = e.document_id
            WHERE e.source_type IN ('google_vision', 'ai_vision')
              {clause}
            ORDER BY e.id
            """
        ).fetchall()

    if not rows:
        print("Nothing to enrich.")
        return 0

    config = load_pipeline_config()
    enriched = fail = 0
    with connect() as conn:
        for doc_id, ext_id, raw_text, owncloud_path, source_path in rows:
            filename = Path(owncloud_path or source_path or "unknown").name
            try:
                enrich_extraction_from_ocr_text(
                    conn,
                    int(ext_id),
                    raw_text or "",
                    filename,
                    "vision",
                    config,
                )
                enriched += 1
                print(f"[ENRICH] doc_id={doc_id} ext_id={ext_id}")
            except Exception as exc:
                fail += 1
                print(f"[FAIL] doc_id={doc_id} ext_id={ext_id} {exc}")
            if args.sleep_seconds > 0:
                time.sleep(args.sleep_seconds)

    print(f"Vision enrich: ok={enriched} fail={fail}")

    if not args.resync_teable:
        return 0 if fail == 0 else 2

    with connect() as conn:
        all_rows = conn.execute(
            """
            SELECT document_id, id FROM document_extractions
            WHERE source_type IN ('google_vision', 'ai_vision')
            ORDER BY id
            """
        ).fetchall()
    ctx = TeableSyncContext.load()
    tok = fail = 0
    for doc_id, ext_id in all_rows:
        result = sync_extraction_and_document(ctx, int(doc_id), int(ext_id))
        if result.get("error"):
            fail += 1
        else:
            tok += 1
    print(f"Teable resync: ok={tok} fail={fail}")
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
