#!/usr/bin/env python3
"""Mirror PostgreSQL catalog rows to Teable via REST API (UI layer, not SoT)."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import unicodedata
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workspace.ocr_pipeline.db_postgres import connect, load_dotenv

ENV_FILE = REPO_ROOT / ".env"
TEABLE_STATUS_OPTIONS = ("To do", "In progress", "Done")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=0, help="Max rows to sync (0 = all).")
    parser.add_argument(
        "--drive-prefix",
        default="project/hth-shared-drive",
        help="Only sync documents whose owncloud_path starts with this prefix.",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--sleep-seconds", type=float, default=0.2)
    return parser.parse_args()


def teable_config() -> dict[str, str]:
    load_dotenv(ENV_FILE)
    url = os.environ.get("TEABLE_API_URL", "").rstrip("/")
    token = os.environ.get("TEABLE_API_TOKEN", "").strip()
    table_id = os.environ.get("TEABLE_TABLE_DOCUMENTS_ID", "").strip()
    if not url or not token or not table_id:
        raise RuntimeError("TEABLE_API_URL, TEABLE_API_TOKEN, TEABLE_TABLE_DOCUMENTS_ID required in .env")
    return {
        "url": url,
        "token": token,
        "table_id": table_id,
        "field_label": os.environ.get("TEABLE_FIELD_LABEL", "Label"),
        "field_number": os.environ.get("TEABLE_FIELD_NUMBER", "Number"),
        "field_status": os.environ.get("TEABLE_FIELD_STATUS", "Status"),
    }


def display_path(path: str | None) -> str:
    if not path:
        return ""
    return unicodedata.normalize("NFC", unquote(path))


def map_teable_status(status: str, ai_review_status: str | None) -> str:
    if status == "success" and ai_review_status == "success":
        return "Done"
    if status == "success":
        return "In progress"
    return "To do"


def build_label(doc_id: int, owncloud_path: str | None, ai_category: str | None) -> str:
    path = display_path(owncloud_path)
    name = Path(path).name if path else f"doc-{doc_id}"
    if ai_category:
        return f"{name} — {ai_category}"
    return name


def teable_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def fetch_existing_by_number(cfg: dict[str, str]) -> dict[int, str]:
    """Return doc_id -> Teable record id."""
    out: dict[int, str] = {}
    skip = 0
    take = 1000
    field_number = cfg["field_number"]
    endpoint = f"{cfg['url']}/table/{cfg['table_id']}/record"
    while True:
        params = {"fieldKeyType": "name", "take": take, "skip": skip}
        response = requests.get(
            endpoint,
            headers=teable_headers(cfg["token"]),
            params=params,
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        records = payload.get("records", [])
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


def select_documents(drive_prefix: str, limit: int) -> list[tuple[Any, ...]]:
    sql = """
        SELECT
            id, owncloud_path, status, ai_category, ai_review_status, updated_at
        FROM documents
        WHERE owncloud_path LIKE %s
        ORDER BY id
    """
    params: list[Any] = [f"{drive_prefix}%"]
    if limit > 0:
        sql += " LIMIT %s"
        params.append(limit)
    with connect() as conn:
        return conn.execute(sql, params).fetchall()


def upsert_record(
    cfg: dict[str, str],
    fields: dict[str, Any],
    record_id: str | None,
    dry_run: bool,
) -> str:
    if dry_run:
        action = "PATCH" if record_id else "POST"
        print(f"[DRY] {action} fields={json.dumps(fields, ensure_ascii=False)}")
        return record_id or "dry-run-id"

    if record_id:
        endpoint = f"{cfg['url']}/table/{cfg['table_id']}/record/{record_id}"
        body = {"fieldKeyType": "name", "record": {"fields": fields}}
        response = requests.patch(
            endpoint,
            headers=teable_headers(cfg["token"]),
            json=body,
            timeout=60,
        )
        response.raise_for_status()
        return record_id

    endpoint = f"{cfg['url']}/table/{cfg['table_id']}/record"
    body = {"fieldKeyType": "name", "records": [{"fields": fields}]}
    response = requests.post(
        endpoint,
        headers=teable_headers(cfg["token"]),
        json=body,
        timeout=60,
    )
    response.raise_for_status()
    created = response.json().get("records", [])
    if not created:
        raise RuntimeError("Teable create returned no records")
    return str(created[0]["id"])


def main() -> int:
    args = parse_args()
    cfg = teable_config()
    batch_started = datetime.now(UTC)
    t0 = time.perf_counter()

    rows = select_documents(args.drive_prefix, args.limit)
    if not rows:
        print("No documents matched drive prefix.")
        return 0

    existing = fetch_existing_by_number(cfg)
    created = updated = failed = 0

    for doc_id, owncloud_path, status, ai_category, ai_review_status, _updated_at in rows:
        fields = {
            cfg["field_label"]: build_label(doc_id, owncloud_path, ai_category),
            cfg["field_number"]: doc_id,
            cfg["field_status"]: map_teable_status(status or "", ai_review_status),
        }
        record_id = existing.get(doc_id)
        try:
            new_id = upsert_record(cfg, fields, record_id, args.dry_run)
            if record_id:
                updated += 1
                print(f"[PATCH] doc_id={doc_id} teable={record_id}")
            else:
                created += 1
                existing[doc_id] = new_id
                print(f"[POST] doc_id={doc_id} teable={new_id}")
        except Exception as exc:
            failed += 1
            print(f"[FAIL] doc_id={doc_id}: {exc}")

        if args.sleep_seconds > 0:
            time.sleep(args.sleep_seconds)

    duration = round(time.perf_counter() - t0, 3)
    batch_finished = datetime.now(UTC)
    print(
        f"Teable sync end: {batch_finished.isoformat()} "
        f"duration={duration}s rows={len(rows)} created={created} "
        f"updated={updated} failed={failed}"
    )
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
