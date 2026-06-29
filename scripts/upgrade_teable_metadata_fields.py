#!/usr/bin/env python3
"""Replace text AI fields on Teable with singleSelect / multipleSelect + choices."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workspace.ocr_pipeline.db_postgres import connect, load_dotenv
from workspace.ocr_pipeline.metadata_normalize import merge_discovered_choices
from workspace.ocr_pipeline.teable_catalog import list_table_fields, teable_headers

ENV_FILE = REPO_ROOT / ".env"

TYPED_FIELDS: tuple[tuple[str, str], ...] = (
    ("ai_category", "singleSelect"),
    ("ai_doc_type", "singleSelect"),
    ("ai_tags", "multipleSelect"),
)

LEGACY_NAMES = ("category", "tags")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--table", choices=("owncloud", "extractions", "both"), default="both")
    return parser.parse_args()


def teable_tables(cfg: dict[str, str], which: str) -> list[tuple[str, str]]:
    tables: list[tuple[str, str]] = []
    if which in ("owncloud", "both"):
        tables.append(("OwnCloud", cfg["documents_table_id"]))
    if which in ("extractions", "both"):
        tables.append(("DocExtractions", cfg["extractions_table_id"]))
    return tables


def teable_env() -> dict[str, str]:
    load_dotenv(ENV_FILE)
    return {
        "url": os.environ["TEABLE_API_URL"].rstrip("/"),
        "token": os.environ["TEABLE_API_TOKEN"],
        "documents_table_id": os.environ["TEABLE_TABLE_DOCUMENTS_ID"],
        "extractions_table_id": os.environ["TEABLE_TABLE_EXTRACTIONS_ID"],
    }


def gather_choices_from_postgres() -> dict[str, list[str]]:
    with connect() as conn:
        doc_rows = conn.execute(
            "SELECT ai_category, ai_doc_type, ai_tags FROM documents"
        ).fetchall()
        ext_rows = conn.execute(
            "SELECT category, doc_type, tags FROM document_extractions"
        ).fetchall()
    categories = [r[0] for r in doc_rows] + [r[0] for r in ext_rows]
    doc_types = [r[1] for r in doc_rows] + [r[1] for r in ext_rows]
    tag_lists = [r[2] for r in doc_rows] + [r[2] for r in ext_rows]
    return merge_discovered_choices(categories, doc_types, tag_lists)


def delete_field(cfg: dict[str, str], table_id: str, field_id: str, name: str, dry_run: bool) -> None:
    if dry_run:
        print(f"[DRY] DELETE FIELD {name} ({field_id})")
        return
    response = requests.delete(
        f"{cfg['url']}/table/{table_id}/field/{field_id}",
        headers=teable_headers(cfg["token"]),
        timeout=60,
    )
    response.raise_for_status()
    print(f"[DEL] field {name}")


def create_typed_field(
    cfg: dict[str, str],
    table_id: str,
    name: str,
    field_type: str,
    choices: list[str],
    dry_run: bool,
) -> None:
    existing = {f["name"]: f for f in list_table_fields({**cfg, "table_id": table_id})}
    if name in existing and existing[name]["type"] == field_type:
        print(f"[SKIP] {name} already {field_type}")
        return
    body: dict[str, Any] = {
        "name": name,
        "type": field_type,
        "options": {
            "choices": [{"name": choice, "color": "blue"} for choice in choices],
        },
    }
    if dry_run:
        print(f"[DRY] CREATE {name} {field_type} choices={len(choices)}")
        return
    response = requests.post(
        f"{cfg['url']}/table/{table_id}/field",
        headers=teable_headers(cfg["token"]),
        json=body,
        timeout=120,
    )
    response.raise_for_status()
    print(f"[FIELD] {name} {field_type} choices={len(choices)} id={response.json().get('id')}")


def upgrade_table(
    cfg: dict[str, str],
    table_label: str,
    table_id: str,
    choices: dict[str, list[str]],
    dry_run: bool,
) -> None:
    fields = list_table_fields({**cfg, "table_id": table_id})
    by_name = {f["name"]: f for f in fields}
    to_delete: list[tuple[str, str]] = []
    for name, field in by_name.items():
        if name in {n for n, _ in TYPED_FIELDS} and field["type"] in {
            "singleLineText",
            "longText",
        }:
            to_delete.append((name, field["id"]))
        if name in LEGACY_NAMES:
            to_delete.append((name, field["id"]))
    for name, field_id in to_delete:
        delete_field(cfg, table_id, field_id, name, dry_run)
    for name, field_type in TYPED_FIELDS:
        create_typed_field(cfg, table_id, name, field_type, choices[name], dry_run)
    print(f"[OK] upgraded {table_label} ({table_id})")


def main() -> int:
    args = parse_args()
    cfg = teable_env()
    choices = gather_choices_from_postgres()
    print(
        f"Choices: category={len(choices['ai_category'])} "
        f"doc_type={len(choices['ai_doc_type'])} tags={len(choices['ai_tags'])}"
    )
    for label, table_id in teable_tables(cfg, args.table):
        upgrade_table(cfg, label, table_id, choices, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
