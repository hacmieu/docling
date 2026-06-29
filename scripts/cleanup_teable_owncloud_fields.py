#!/usr/bin/env python3
"""Remove redundant OwnCloud Teable fields (metadata now lives on DocExtractions)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workspace.ocr_pipeline.teable_catalog import (
    REDUNDANT_OWN_CLOUD_FIELDS,
    delete_table_field,
    list_table_fields,
    teable_config,
)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--fields",
        nargs="*",
        default=None,
        help="Override field names to delete (default: REDUNDANT_OWN_CLOUD_FIELDS).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cfg = teable_config()
    targets = set(args.fields or REDUNDANT_OWN_CLOUD_FIELDS)
    fields = list_table_fields(cfg)
    deleted = 0
    for field in fields:
        name = field.get("name")
        if name not in targets:
            continue
        field_id = str(field["id"])
        try:
            if args.dry_run:
                print(f"[DRY] DELETE field {name} id={field_id}")
                deleted += 1
                continue
            delete_table_field(cfg, field_id)
            print(f"[DELETE] {name} id={field_id}")
            deleted += 1
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 404:
                print(f"[SKIP] {name} id={field_id} (not found)")
                continue
            raise
    print(f"Done: {deleted} field(s) {'would be ' if args.dry_run else ''}removed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
