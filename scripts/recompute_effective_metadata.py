#!/usr/bin/env python3
"""Recompute effective extraction cache on documents and optionally PATCH Teable OwnCloud."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workspace.ocr_pipeline.db_postgres import connect, load_dotenv
from workspace.ocr_pipeline.extraction_priority import SOURCE_LABELS_VI
from workspace.ocr_pipeline.teable_catalog import (
    DRIVE_PREFIX_DEFAULT,
    teable_config,
    teable_headers,
)

MIGRATION_005 = (
    REPO_ROOT / "workspace/ocr_pipeline/infra/postgres/migrations/005_documents_effective_cache.sql"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--sync-teable",
        action="store_true",
        help="PATCH active_priority, active_source, extraction_version_count on Teable OwnCloud.",
    )
    parser.add_argument("--drive-prefix", default=DRIVE_PREFIX_DEFAULT)
    parser.add_argument("--sleep-seconds", type=float, default=0.12)
    return parser.parse_args()


def apply_migration(conn) -> None:
    if not MIGRATION_005.exists():
        raise FileNotFoundError(MIGRATION_005)
    conn.execute(MIGRATION_005.read_text(encoding="utf-8"))


def recompute_postgres(conn, dry_run: bool) -> tuple[int, int]:
    if dry_run:
        row = conn.execute(
            """
            SELECT COUNT(*) FROM documents d
            JOIN effective_document_extractions e ON e.document_id = d.id
            """
        ).fetchone()
        return int(row[0]), 0

    apply_migration(conn)
    updated = conn.execute(
        """
        UPDATE documents d
        SET
            effective_extraction_id = e.extraction_id,
            effective_source_type = e.source_type,
            effective_priority = e.priority_score
        FROM effective_document_extractions e
        WHERE d.id = e.document_id
        """
    ).rowcount
    cleared = conn.execute(
        """
        UPDATE documents d
        SET
            effective_extraction_id = NULL,
            effective_source_type = NULL,
            effective_priority = NULL
        WHERE NOT EXISTS (
            SELECT 1 FROM effective_document_extractions e WHERE e.document_id = d.id
        )
        """
    ).rowcount
    return int(updated or 0), int(cleared or 0)


def fetch_teable_index(cfg: dict[str, str]) -> dict[int, str]:
    out: dict[int, str] = {}
    skip = 0
    take = 1000
    field_number = cfg["field_number"]
    endpoint = f"{cfg['url']}/table/{cfg['table_id']}/record"
    while True:
        response = requests.get(
            endpoint,
            headers=teable_headers(cfg["token"]),
            params={"fieldKeyType": "name", "take": take, "skip": skip},
            timeout=60,
        )
        response.raise_for_status()
        records = response.json().get("records", [])
        if not records:
            break
        for record in records:
            fields = record.get("fields") or {}
            number = fields.get(field_number)
            if number is not None:
                try:
                    out[int(number)] = str(record["id"])
                except (TypeError, ValueError, KeyError):
                    continue
        if len(records) < take:
            break
        skip += take
    return out


def select_sync_rows(drive_prefix: str) -> list[tuple[Any, ...]]:
    sql = """
        SELECT
            d.id,
            d.effective_source_type,
            d.effective_priority,
            COALESCE(v.cnt, 0) AS extraction_version_count
        FROM documents d
        LEFT JOIN (
            SELECT document_id, COUNT(*) AS cnt
            FROM document_extractions
            GROUP BY document_id
        ) v ON v.document_id = d.id
        WHERE d.owncloud_path LIKE %s
        ORDER BY d.id
    """
    with connect() as conn:
        return conn.execute(sql, (f"{drive_prefix}%",)).fetchall()


def patch_teable_record(
    cfg: dict[str, str],
    record_id: str,
    fields: dict[str, Any],
    dry_run: bool,
) -> None:
    if dry_run:
        print(f"[DRY] PATCH {record_id} {json.dumps(fields, ensure_ascii=False)}")
        return
    endpoint = f"{cfg['url']}/table/{cfg['table_id']}/record/{record_id}"
    body = {"fieldKeyType": "name", "record": {"fields": fields}}
    response = requests.patch(
        endpoint,
        headers=teable_headers(cfg["token"]),
        json=body,
        timeout=60,
    )
    response.raise_for_status()


def sync_teable(drive_prefix: str, dry_run: bool, sleep_seconds: float) -> tuple[int, int]:
    cfg = teable_config()
    index = fetch_teable_index(cfg)
    rows = select_sync_rows(drive_prefix)
    patched = skipped = 0
    for doc_id, source_type, priority, version_count in rows:
        record_id = index.get(doc_id)
        if not record_id:
            skipped += 1
            continue
        fields: dict[str, Any] = {"extraction_version_count": int(version_count)}
        if priority is not None:
            fields["active_priority"] = int(priority)
        if source_type:
            fields["active_source"] = source_type
        try:
            patch_teable_record(cfg, record_id, fields, dry_run)
            patched += 1
            if patched % 50 == 0:
                print(f"[TEABLE] patched {patched} rows…")
        except Exception as exc:
            print(f"[FAIL] doc_id={doc_id}: {exc}")
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)
    return patched, skipped


def main() -> int:
    load_dotenv()
    args = parse_args()
    with connect() as conn:
        updated, cleared = recompute_postgres(conn, args.dry_run)
    print(f"Postgres effective cache: updated={updated} cleared={cleared} dry_run={args.dry_run}")

    if args.sync_teable:
        patched, skipped = sync_teable(args.drive_prefix, args.dry_run, args.sleep_seconds)
        print(f"Teable PATCH: patched={patched} skipped_no_record={skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
