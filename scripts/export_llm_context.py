#!/usr/bin/env python3
"""Export compact LLM context packs from catalog metadata (token-estimated)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workspace.ocr_pipeline.db_postgres import load_dotenv
from workspace.ocr_pipeline.llm_context_pack import (
    build_llm_context_pack,
    search_by_doc_types,
    search_staff_documents,
)

DEGREE_DOC_TYPES = [
    "bang-tot-nghiep",
    "chung-chi-hanh-nghe",
    "chung-chi-dao-tao",
    "chung-chi-dao-tao-lien-tuc",
    "chung-chi-ao-tao-lien-tuc",
    "chung-chi",
    "ban-sao-bang-cap",
]


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)

    staff = sub.add_parser("staff", help="All documents for a staff member by name")
    staff.add_argument("name", help="e.g. Trần Đức Hiển")
    staff.add_argument("--phong-ban", default=None)
    staff.add_argument("--limit", type=int, default=50)
    staff.add_argument("-o", "--output", type=Path, default=None)

    degrees = sub.add_parser("degrees", help="Doctor degrees/certificates in catalog")
    degrees.add_argument("--path-contains", default="BÁC SĨ", help="OwnCloud path filter")
    degrees.add_argument("--phong-ban", default=None)
    degrees.add_argument("--all-catalog", action="store_true", help="Ignore path filter")
    degrees.add_argument("--limit", type=int, default=200)
    degrees.add_argument("-o", "--output", type=Path, default=None)

    args = parser.parse_args()

    if args.mode == "staff":
        docs = search_staff_documents(args.name, phong_ban=args.phong_ban, limit=args.limit)
        pack = build_llm_context_pack(
            f"Tất cả thông tin của {args.name}",
            docs,
            filter_meta={"name": args.name, "phong_ban": args.phong_ban},
        )
    else:
        path_filter = None if args.all_catalog else args.path_contains
        docs = search_by_doc_types(
            DEGREE_DOC_TYPES,
            path_contains=path_filter,
            phong_ban=args.phong_ban,
            limit=args.limit,
        )
        pack = build_llm_context_pack(
            "Tất cả bằng cấp/chứng chỉ bác sĩ",
            docs,
            filter_meta={
                "doc_types": DEGREE_DOC_TYPES,
                "path_contains": path_filter,
                "phong_ban": args.phong_ban,
            },
        )

    out = args.output
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote {out} ({pack['doc_count']} docs, ~{pack['estimated_tokens_prompt']} tokens prompt)")
    else:
        print(json.dumps(pack, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
