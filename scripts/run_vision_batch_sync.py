#!/usr/bin/env python3
"""DEV: batch Gemini vision OCR synchronously (parallel lane vs DeepSeek enrich)."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workspace.ocr_pipeline.db_postgres import connect, load_dotenv
from workspace.ocr_pipeline.tasks.vision_tasks import vision_ocr_document

DEFAULT_LOG = REPO_ROOT / "workspace/ocr_pipeline/09_logs"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--doc-id", type=int, action="append", default=[])
    parser.add_argument("--drive-prefix", default="project/hth-shared-drive")
    parser.add_argument("--sleep-seconds", type=float, default=12.0, help="Slow free-tier pacing")
    parser.add_argument("--skip-existing", action="store_true", default=True)
    parser.add_argument("--log-file", type=Path, default=None)
    return parser.parse_args()


def select_doc_ids(
    doc_ids: list[int],
    drive_prefix: str,
    limit: int,
    skip_existing: bool,
) -> list[int]:
    if doc_ids:
        return doc_ids
    skip_clause = ""
    if skip_existing:
        skip_clause = """
          AND NOT EXISTS (
            SELECT 1 FROM document_extractions e
            WHERE e.document_id = d.id AND e.source_type = 'google_vision'
          )
        """
    sql = f"""
        SELECT d.id FROM documents d
        WHERE d.owncloud_path LIKE %s
          AND d.local_path IS NOT NULL AND d.local_path != ''
          AND d.status = 'success'
          {skip_clause}
        ORDER BY d.id
    """
    params: list[object] = [f"{drive_prefix}%"]
    if limit > 0:
        sql += " LIMIT %s"
        params.append(limit)
    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [int(r[0]) for r in rows]


def log_line(log_file: Path | None, message: str) -> None:
    print(message, flush=True)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with log_file.open("a", encoding="utf-8") as handle:
            handle.write(message + "\n")


def main() -> int:
    load_dotenv()
    args = parse_args()
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    log_file = args.log_file or (DEFAULT_LOG / f"{stamp}-vision-batch.log")
    ids = select_doc_ids(args.doc_id, args.drive_prefix, args.limit, args.skip_existing)
    if not ids:
        log_line(log_file, "No documents for vision OCR.")
        return 0

    ok = fail = 0
    t0 = time.perf_counter()
    log_line(log_file, f"Vision batch start: {len(ids)} doc(s) at {datetime.now(UTC).isoformat()}")

    for doc_id in ids:
        started = datetime.now(UTC).isoformat()
        log_line(log_file, f"[VISION] doc_id={doc_id} started={started}")
        result = vision_ocr_document(doc_id)
        if result.get("ok"):
            ok += 1
            log_line(
                log_file,
                f"[OK] doc_id={doc_id} extraction_id={result.get('extraction_id')} "
                f"text_len={result.get('text_len')}",
            )
        else:
            fail += 1
            log_line(log_file, f"[FAIL] doc_id={doc_id} error={result.get('error')}")
        if args.sleep_seconds > 0:
            time.sleep(args.sleep_seconds)

    duration = round(time.perf_counter() - t0, 1)
    summary = (
        f"Vision batch end: ok={ok} fail={fail} duration={duration}s "
        f"finished={datetime.now(UTC).isoformat()}"
    )
    log_line(log_file, summary)
    report = {
        "started_at": datetime.fromtimestamp(t0, UTC).isoformat(),
        "finished_at": datetime.now(UTC).isoformat(),
        "duration_seconds": duration,
        "ok": ok,
        "fail": fail,
        "doc_ids": ids,
    }
    report_path = log_file.with_suffix(".json")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    log_line(log_file, f"Report: {report_path}")
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
