#!/usr/bin/env python3
"""Sync Postgres document_extractions (RAW + DeepSeek) to Teable DocExtractions."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workspace.ocr_pipeline.db_postgres import connect, load_dotenv
from workspace.ocr_pipeline.extraction_priority import SOURCE_LABELS_VI
from workspace.ocr_pipeline.metadata_normalize import normalize_category, normalize_tags
from workspace.ocr_pipeline.teable_catalog import MARKDOWN_PREVIEW_LEN, teable_headers

ENV_FILE = REPO_ROOT / ".env"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument(
        "--source-type",
        action="append",
        choices=["local_llm_ocr", "deepseek_cleanup"],
        help="Filter source types (default: both RAW and DeepSeek).",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--sleep-seconds", type=float, default=0.1)
    return parser.parse_args()


def teable_env() -> dict[str, str]:
    load_dotenv(ENV_FILE)
    return {
        "url": os.environ["TEABLE_API_URL"].rstrip("/"),
        "token": os.environ["TEABLE_API_TOKEN"],
        "documents_table_id": os.environ["TEABLE_TABLE_DOCUMENTS_ID"],
        "extractions_table_id": os.environ["TEABLE_TABLE_EXTRACTIONS_ID"],
        "field_number": os.environ.get("TEABLE_FIELD_NUMBER", "Number"),
    }


def fetch_doc_record_map(cfg: dict[str, str]) -> dict[int, str]:
    out: dict[int, str] = {}
    skip = 0
    take = 1000
    endpoint = f"{cfg['url']}/table/{cfg['documents_table_id']}/record"
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
            number = (record.get("fields") or {}).get(cfg["field_number"])
            if number is not None:
                try:
                    out[int(number)] = str(record["id"])
                except (TypeError, ValueError):
                    pass
        if len(records) < take:
            break
        skip += take
    return out


def fetch_extraction_record_map(cfg: dict[str, str]) -> dict[int, str]:
    out: dict[int, str] = {}
    skip = 0
    take = 1000
    endpoint = f"{cfg['url']}/table/{cfg['extractions_table_id']}/record"
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
            pg_id = (record.get("fields") or {}).get("postgres_extraction_id")
            if pg_id is not None:
                try:
                    out[int(pg_id)] = str(record["id"])
                except (TypeError, ValueError):
                    pass
        if len(records) < take:
            break
        skip += take
    return out


def fetch_allowed_select_choices(cfg: dict[str, str]) -> dict[str, set[str]]:
    endpoint = f"{cfg['url']}/table/{cfg['extractions_table_id']}/field"
    response = requests.get(endpoint, headers=teable_headers(cfg["token"]), timeout=60)
    response.raise_for_status()
    fields = response.json()
    out: dict[str, set[str]] = {}
    for field in fields:
        name = str(field.get("name") or "")
        options = field.get("options") or {}
        choices = options.get("choices") or []
        if not name or not choices:
            continue
        out[name] = {str(choice.get("name")) for choice in choices if choice.get("name")}
    return out


def version_label(source_type: str, version_no: int) -> str:
    if source_type == "local_llm_ocr":
        return f"RAW-v{version_no}"
    if source_type == "deepseek_cleanup":
        return f"DeepSeek-v{version_no}"
    return f"{source_type}-v{version_no}"


def build_fields(
    row: tuple[Any, ...],
    doc_record_id: str | None,
    allowed_choices: dict[str, set[str]],
) -> dict[str, Any]:
    (
        ext_id,
        document_id,
        version_no,
        source_type,
        priority_score,
        version_status,
        category,
        doc_type,
        tags,
        key_fields,
        extracted_summary,
        raw_text,
        model_name,
        created_by,
        created_at,
    ) = row
    _cat_slug, cat_label = normalize_category(category)
    norm_tags = normalize_tags(tags)
    fields: dict[str, Any] = {
        "version_label": version_label(source_type, version_no),
        "postgres_extraction_id": ext_id,
        "doc_id": document_id,
        "source_type": source_type,
        "priority": priority_score,
        "version_status": version_status,
        "key_fields_json": json.dumps(key_fields or {}, ensure_ascii=False),
        "extracted_summary": extracted_summary or "",
        "raw_text_preview": (raw_text or "")[:MARKDOWN_PREVIEW_LEN],
        "model_name": model_name or "",
        "created_by": created_by or "",
        "created_at": created_at.isoformat() if created_at else "",
    }
    if cat_label and cat_label in allowed_choices.get("ai_category", set()):
        fields["ai_category"] = cat_label
    if doc_type and doc_type in allowed_choices.get("ai_doc_type", set()):
        fields["ai_doc_type"] = doc_type
    if norm_tags:
        allowed_tags = allowed_choices.get("ai_tags", set())
        valid_tags = [tag for tag in norm_tags if tag in allowed_tags]
        if valid_tags:
            fields["ai_tags"] = valid_tags
    if doc_record_id:
        fields["document"] = {"id": doc_record_id}
    return fields


def upsert_record(
    cfg: dict[str, str],
    fields: dict[str, Any],
    record_id: str | None,
    dry_run: bool,
) -> str:
    if dry_run:
        return record_id or "dry"
    if record_id:
        endpoint = f"{cfg['url']}/table/{cfg['extractions_table_id']}/record/{record_id}"
        body = {"fieldKeyType": "name", "record": {"fields": fields}}
        response = requests.patch(
            endpoint, headers=teable_headers(cfg["token"]), json=body, timeout=60
        )
        response.raise_for_status()
        return record_id
    endpoint = f"{cfg['url']}/table/{cfg['extractions_table_id']}/record"
    body = {"fieldKeyType": "name", "records": [{"fields": fields}]}
    response = requests.post(
        endpoint, headers=teable_headers(cfg["token"]), json=body, timeout=60
    )
    response.raise_for_status()
    return str(response.json()["records"][0]["id"])


def select_extractions(source_types: list[str] | None, limit: int) -> list[tuple[Any, ...]]:
    type_filter = "e.source_type IN ('local_llm_ocr', 'deepseek_cleanup')"
    params: list[Any] = []
    if source_types:
        placeholders = ", ".join(["%s"] * len(source_types))
        type_filter = f"e.source_type IN ({placeholders})"
        params = list(source_types)
    sql = f"""
        SELECT
            e.id, e.document_id, e.version_no, e.source_type, e.priority_score,
            e.version_status, e.category, e.doc_type, e.tags, e.key_fields,
            e.extracted_summary, e.raw_text, e.model_name, e.created_by, e.created_at
        FROM document_extractions e
        JOIN documents d ON d.id = e.document_id
        WHERE {type_filter}
          AND d.owncloud_path LIKE %s
        ORDER BY e.document_id, e.version_no
    """
    params.append("project/hth-shared-drive%")
    if limit > 0:
        sql += " LIMIT %s"
        params.append(limit)
    with connect() as conn:
        return conn.execute(sql, params).fetchall()


def main() -> int:
    args = parse_args()
    cfg = teable_env()
    source_types = args.source_type or None
    rows = select_extractions(source_types, args.limit)
    if not rows:
        print("No extractions to sync.")
        return 0

    doc_map = fetch_doc_record_map(cfg)
    ext_map = fetch_extraction_record_map(cfg)
    allowed_choices = fetch_allowed_select_choices(cfg)
    created = updated = failed = skipped = 0
    t0 = time.perf_counter()

    with connect() as conn:
        for row in rows:
            ext_id = row[0]
            doc_id = row[1]
            doc_record = doc_map.get(doc_id)
            if not doc_record:
                skipped += 1
                print(f"[SKIP] ext_id={ext_id} doc_id={doc_id} missing OwnCloud link")
                continue
            fields = build_fields(row, doc_record, allowed_choices)
            record_id = ext_map.get(ext_id)
            try:
                teable_id = upsert_record(cfg, fields, record_id, args.dry_run)
                if not args.dry_run:
                    conn.execute(
                        "UPDATE document_extractions SET teable_record_id = %s WHERE id = %s",
                        (teable_id, ext_id),
                    )
                if record_id:
                    updated += 1
                else:
                    created += 1
                    ext_map[ext_id] = teable_id
                if (created + updated) % 50 == 0:
                    print(f"[PROGRESS] created={created} updated={updated}")
            except Exception as exc:
                failed += 1
                print(f"[FAIL] ext_id={ext_id}: {exc}")
            if args.sleep_seconds > 0:
                time.sleep(args.sleep_seconds)

    duration = round(time.perf_counter() - t0, 3)
    print(
        f"Extraction sync end duration={duration}s total={len(rows)} "
        f"created={created} updated={updated} skipped={skipped} failed={failed}"
    )
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
