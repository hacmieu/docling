#!/usr/bin/env python3
"""Audit Teable tables against canonical ERD (OwnCloud + DocExtractions)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workspace.ocr_pipeline.db_postgres import load_dotenv
from workspace.ocr_pipeline.teable_catalog import (
    CANONICAL_OWN_CLOUD_FIELD_NAMES,
    EXTENDED_CATALOG_FIELDS,
    REDUNDANT_OWN_CLOUD_FIELDS,
    list_table_fields,
    teable_config,
    teable_headers,
)

ENV_FILE = REPO_ROOT / ".env"

CANONICAL_EXTRACTION_FIELD_NAMES: frozenset[str] = frozenset(
    {
        "version_label",
        "postgres_extraction_id",
        "doc_id",
        "source_type",
        "priority",
        "version_status",
        "ai_category",
        "ai_doc_type",
        "ai_tags",
        "key_fields_json",
        "extracted_summary",
        "raw_text_preview",
        "model_name",
        "created_by",
        "created_at",
        "document",
        "prompt_name",
    }
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable summary only.",
    )
    return parser.parse_args()


def extractions_table_id() -> str:
    load_dotenv(ENV_FILE)
    return os.environ["TEABLE_TABLE_EXTRACTIONS_ID"].strip()


def audit_owncloud(cfg: dict[str, str]) -> dict[str, object]:
    fields = list_table_fields(cfg)
    names = {str(f.get("name")) for f in fields}
    label = cfg.get("field_label", "Label")
    number = cfg.get("field_number", "Number")
    status = cfg.get("field_status", "Status")
    canonical = set(CANONICAL_OWN_CLOUD_FIELD_NAMES) | {label, number, status}
    extended = {spec.name for spec in EXTENDED_CATALOG_FIELDS}
    required = canonical | extended
    missing = sorted(required - names)
    redundant = sorted((names & set(REDUNDANT_OWN_CLOUD_FIELDS)) | (names - required - {"DocExtractions"}))
    orphan_links = [
        f["name"]
        for f in fields
        if f.get("type") == "link"
        and f.get("name") != "DocExtractions"
        and str(f.get("name", "")).startswith("_")
    ]
    doc_link = next((f for f in fields if f.get("name") == "DocExtractions"), None)
    link_ok = bool(
        doc_link
        and (doc_link.get("options") or {}).get("foreignTableId") == extractions_table_id()
    )
    return {
        "table": "OwnCloud",
        "field_count": len(names),
        "missing_required": missing,
        "redundant_or_noncanonical": redundant,
        "orphan_link_fields": orphan_links,
        "doc_extractions_link_ok": link_ok,
        "ready": not missing and not redundant and not orphan_links and link_ok,
    }


def audit_extractions(cfg: dict[str, str]) -> dict[str, object]:
    table_id = extractions_table_id()
    import requests

    endpoint = f"{cfg['url']}/table/{table_id}/field"
    response = requests.get(endpoint, headers=teable_headers(cfg["token"]), timeout=60)
    response.raise_for_status()
    fields = response.json()
    names = {str(f.get("name")) for f in fields}
    missing = sorted(CANONICAL_EXTRACTION_FIELD_NAMES - names)
    extra = sorted(names - CANONICAL_EXTRACTION_FIELD_NAMES)
    return {
        "table": "DocExtractions",
        "field_count": len(names),
        "missing_required": missing,
        "extra_fields": extra,
        "ready": not missing,
    }


def main() -> int:
    args = parse_args()
    cfg = teable_config()
    own = audit_owncloud(cfg)
    ext = audit_extractions(cfg)
    ready = bool(own["ready"]) and bool(ext["ready"])
    if args.json:
        import json

        print(json.dumps({"owncloud": own, "extractions": ext, "ready": ready}, ensure_ascii=False, indent=2))
        return 0 if ready else 2

    print("=== Teable ERD audit ===")
    for report in (own, ext):
        print(f"\n[{report['table']}] fields={report['field_count']} ready={report['ready']}")
        for key in ("missing_required", "redundant_or_noncanonical", "orphan_link_fields", "extra_fields"):
            if key in report and report[key]:
                print(f"  {key}: {report[key]}")
        if "doc_extractions_link_ok" in report:
            print(f"  doc_extractions_link_ok: {report['doc_extractions_link_ok']}")
    print(f"\nOverall ERD ready: {ready}")
    return 0 if ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
