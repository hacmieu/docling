#!/usr/bin/env python3
"""Ensure Teable OwnCloud table has full catalog fields (create missing via API)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workspace.ocr_pipeline.teable_catalog import ensure_catalog_fields, list_table_fields, teable_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--list", action="store_true", help="List current fields and exit.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cfg = teable_config()
    if args.list:
        for field in list_table_fields(cfg):
            print(f"{field['name']}\t{field['type']}\t{field['id']}")
        return 0
    created = ensure_catalog_fields(cfg, dry_run=args.dry_run)
    print(f"Fields created: {len(created)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
