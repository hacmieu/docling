#!/usr/bin/env python3
"""Create Teable tables/fields for multi-version document extraction flow."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workspace.ocr_pipeline.db_postgres import load_dotenv
from workspace.ocr_pipeline.extraction_priority import SOURCE_LABELS_VI, SOURCE_PRIORITY
from workspace.ocr_pipeline.teable_catalog import list_table_fields, teable_headers

ENV_FILE = REPO_ROOT / ".env"

PROMPT_TEMPLATE_FIELDS: list[dict[str, Any]] = [
    {"name": "prompt_name", "type": "singleLineText"},
    {"name": "prompt_slug", "type": "singleLineText"},
    {"name": "prompt_body", "type": "longText"},
    {"name": "doc_type_hint", "type": "singleLineText"},
    {"name": "is_active", "type": "checkbox"},
]

EXTRACTION_FIELDS: list[dict[str, Any]] = [
    {"name": "version_label", "type": "singleLineText"},
    {"name": "postgres_extraction_id", "type": "number"},
    {"name": "doc_id", "type": "number"},
    {
        "name": "source_type",
        "type": "singleSelect",
        "options": {
            "choices": [
                {"name": key, "color": "blue"}
                for key in (
                    "human_verified",
                    "human_webchat",
                    "google_vision",
                    "deepseek_cleanup",
                    "local_llm_ocr",
                )
            ]
        },
    },
    {"name": "priority", "type": "number"},
    {
        "name": "version_status",
        "type": "singleSelect",
        "options": {
            "choices": [
                {"name": "draft", "color": "yellow"},
                {"name": "active", "color": "green"},
                {"name": "superseded", "color": "gray"},
                {"name": "archived", "color": "gray"},
            ]
        },
    },
    {"name": "category", "type": "singleLineText"},
    {"name": "tags", "type": "longText"},
    {"name": "key_fields_json", "type": "longText"},
    {"name": "extracted_summary", "type": "longText"},
    {"name": "raw_text_preview", "type": "longText"},
    {"name": "model_name", "type": "singleLineText"},
    {"name": "prompt_name", "type": "singleLineText"},
    {"name": "created_by", "type": "singleLineText"},
    {"name": "created_at", "type": "singleLineText"},
]

OWNCLOUD_ACTIVE_FIELDS: list[dict[str, Any]] = [
    {"name": "active_priority", "type": "number"},
    {
        "name": "active_source",
        "type": "singleSelect",
        "options": {
            "choices": [{"name": k, "color": "blue"} for k in SOURCE_PRIORITY],
        },
    },
    {"name": "extraction_version_count", "type": "number"},
]

DEFAULT_PROMPTS: list[dict[str, Any]] = [
    {
        "prompt_name": "Hợp đồng lao động",
        "prompt_slug": "hop-dong-lao-dong",
        "prompt_body": (
            "Bóc tách: họ tên, ngày sinh, chức vụ, thời hạn HĐ, mức lương, đơn vị ký. "
            "Trả JSON: category, tags, key_fields {ten, so, ngay, don_vi}."
        ),
        "doc_type_hint": "hop-dong",
        "is_active": True,
    },
    {
        "prompt_name": "Quyết định",
        "prompt_slug": "quyet-dinh",
        "prompt_body": (
            "Bóc tách: số QĐ, ngày ban hành, cơ quan ban hành, trích yếu, người được quyết định."
        ),
        "doc_type_hint": "quyet-dinh",
        "is_active": True,
    },
    {
        "prompt_name": "Phạm vi hành nghề",
        "prompt_slug": "pham-vi-hanh-nghe",
        "prompt_body": (
            "Xác định liên quan phạm vi hành nghề; trích điều khoản, đối tượng, ngày hiệu lực."
        ),
        "doc_type_hint": "quy-dinh",
        "is_active": True,
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--seed-prompts", action="store_true", default=True)
    parser.add_argument("--report", type=Path, default=None, help="Write API permission audit JSON.")
    return parser.parse_args()


def teable_env() -> dict[str, str]:
    load_dotenv(ENV_FILE)
    url = os.environ.get("TEABLE_API_URL", "").rstrip("/")
    token = os.environ.get("TEABLE_API_TOKEN", "").strip()
    base_id = os.environ.get("TEABLE_BASE_ID", "").strip()
    documents_table_id = os.environ.get("TEABLE_TABLE_DOCUMENTS_ID", "").strip()
    if not url or not token or not documents_table_id:
        raise RuntimeError("TEABLE_API_URL, TEABLE_API_TOKEN, TEABLE_TABLE_DOCUMENTS_ID required")
    if not base_id:
        bases = requests.get(f"{url}/base/access/all", headers=teable_headers(token), timeout=60)
        bases.raise_for_status()
        for base in bases.json():
            tables = requests.get(
                f"{url}/base/{base['id']}/table",
                headers=teable_headers(token),
                timeout=60,
            )
            if tables.ok and any(t.get("id") == documents_table_id for t in tables.json()):
                base_id = base["id"]
                break
        if not base_id:
            raise RuntimeError("Could not resolve TEABLE_BASE_ID from documents table")
    return {
        "url": url,
        "token": token,
        "base_id": base_id,
        "documents_table_id": documents_table_id,
        "prompts_table_id": os.environ.get("TEABLE_TABLE_PROMPTS_ID", "").strip(),
        "extractions_table_id": os.environ.get("TEABLE_TABLE_EXTRACTIONS_ID", "").strip(),
    }


def find_table_by_name(cfg: dict[str, str], name: str) -> str | None:
    response = requests.get(
        f"{cfg['url']}/base/{cfg['base_id']}/table",
        headers=teable_headers(cfg["token"]),
        timeout=60,
    )
    response.raise_for_status()
    for table in response.json():
        if table.get("name") == name:
            return str(table["id"])
    return None


def create_table(cfg: dict[str, str], name: str, fields: list[dict[str, Any]], dry_run: bool) -> str:
    existing = find_table_by_name(cfg, name)
    if existing:
        print(f"[TABLE] exists {name} id={existing}")
        return existing
    if dry_run:
        print(f"[DRY] CREATE TABLE {name} fields={len(fields)}")
        return f"dry-{name}"
    response = requests.post(
        f"{cfg['url']}/base/{cfg['base_id']}/table/",
        headers=teable_headers(cfg["token"]),
        json={"name": name, "description": f"HTH OCR catalog — {name}", "fields": fields},
        timeout=120,
    )
    response.raise_for_status()
    table_id = str(response.json()["id"])
    print(f"[TABLE] created {name} id={table_id}")
    return table_id


def ensure_fields_on_table(
    cfg: dict[str, str],
    table_id: str,
    specs: list[dict[str, Any]],
    dry_run: bool,
) -> list[str]:
    existing = {f["name"] for f in list_table_fields({**cfg, "table_id": table_id})}
    created: list[str] = []
    for spec in specs:
        if spec["name"] in existing:
            continue
        if dry_run:
            print(f"[DRY] FIELD {table_id}::{spec['name']}")
            created.append(spec["name"])
            continue
        body = dict(spec)
        if body.get("type") == "number" and "options" not in body:
            body["options"] = {"formatting": {"type": "decimal", "precision": 0}}
        response = requests.post(
            f"{cfg['url']}/table/{table_id}/field",
            headers=teable_headers(cfg["token"]),
            json=body,
            timeout=60,
        )
        response.raise_for_status()
        print(f"[FIELD] {table_id} created {spec['name']} id={response.json().get('id')}")
        created.append(spec["name"])
        existing.add(spec["name"])
    return created


def ensure_link_to_documents(cfg: dict[str, str], child_table_id: str, dry_run: bool) -> None:
    fields = list_table_fields({**cfg, "table_id": child_table_id})
    if any(f.get("type") == "link" for f in fields):
        print(f"[LINK] already on {child_table_id}")
        return
    body = {
        "name": "document",
        "type": "link",
        "options": {
            "relationship": "manyOne",
            "foreignTableId": cfg["documents_table_id"],
        },
    }
    if dry_run:
        print(f"[DRY] LINK {child_table_id} -> OwnCloud")
        return
    response = requests.post(
        f"{cfg['url']}/table/{child_table_id}/field",
        headers=teable_headers(cfg["token"]),
        json=body,
        timeout=60,
    )
    response.raise_for_status()
    print(f"[LINK] created document -> OwnCloud on {child_table_id}")


def seed_prompt_records(cfg: dict[str, str], prompts_table_id: str, dry_run: bool) -> int:
    endpoint = f"{cfg['url']}/table/{prompts_table_id}/record"
    existing_slugs: set[str] = set()
    skip = 0
    while True:
        response = requests.get(
            endpoint,
            headers=teable_headers(cfg["token"]),
            params={"fieldKeyType": "name", "take": 1000, "skip": skip},
            timeout=60,
        )
        response.raise_for_status()
        records = response.json().get("records", [])
        if not records:
            break
        for record in records:
            slug = (record.get("fields") or {}).get("prompt_slug")
            if slug:
                existing_slugs.add(str(slug))
        if len(records) < 1000:
            break
        skip += 1000

    created = 0
    for prompt in DEFAULT_PROMPTS:
        if prompt["prompt_slug"] in existing_slugs:
            continue
        if dry_run:
            print(f"[DRY] PROMPT {prompt['prompt_slug']}")
            created += 1
            continue
        response = requests.post(
            endpoint,
            headers=teable_headers(cfg["token"]),
            json={"fieldKeyType": "name", "records": [{"fields": prompt}]},
            timeout=60,
        )
        response.raise_for_status()
        created += 1
        print(f"[PROMPT] seeded {prompt['prompt_slug']}")
    return created


def api_permission_audit(cfg: dict[str, str]) -> dict[str, Any]:
    token = cfg["token"]
    url = cfg["url"]
    h = teable_headers(token)
    checks: list[dict[str, Any]] = []

    def probe(method: str, path: str, **kwargs: Any) -> None:
        full = f"{url}{path}"
        response = requests.request(method, full, headers=h, timeout=30, **kwargs)
        checks.append(
            {
                "method": method,
                "path": path,
                "status": response.status_code,
                "used_in_setup": response.status_code < 400,
            }
        )

    probe("GET", "/base/access/all")
    probe("GET", f"/base/{cfg['base_id']}/table")
    probe("GET", f"/table/{cfg['documents_table_id']}/field")
    probe("GET", f"/table/{cfg['documents_table_id']}/view")
    probe("GET", f"/table/{cfg['documents_table_id']}/record", params={"take": 1})
    probe("GET", "/space")
    probe("GET", "/auth/user/me")
    return {
        "base_id": cfg["base_id"],
        "documents_table_id": cfg["documents_table_id"],
        "source_priority": SOURCE_PRIORITY,
        "source_labels_vi": SOURCE_LABELS_VI,
        "checks": checks,
        "recommended_keep_permissions": [
            "GET /base/access/all",
            "GET /base/{baseId}/table",
            "POST /base/{baseId}/table/",
            "DELETE /base/{baseId}/table/{tableId}",
            "GET /table/{tableId}/field",
            "POST /table/{tableId}/field",
            "DELETE /table/{tableId}/field/{fieldId}",
            "GET /table/{tableId}/view",
            "GET|POST|PATCH /table/{tableId}/record",
        ],
        "can_disable_after_setup": [
            "DELETE /base/{baseId}/table/{tableId} (if schema frozen)",
            "DELETE /table/{tableId}/field/{fieldId} (if schema frozen)",
            "POST /base/{baseId}/table/ (if no new tables)",
            "POST /table/{tableId}/field (if no new columns)",
        ],
        "already_forbidden": [c for c in checks if c["status"] == 403],
    }


def main() -> int:
    args = parse_args()
    cfg = teable_env()

    prompts_id = cfg["prompts_table_id"] or create_table(
        cfg, "PromptTemplates", PROMPT_TEMPLATE_FIELDS, args.dry_run
    )
    extractions_id = cfg["extractions_table_id"] or create_table(
        cfg, "DocExtractions", EXTRACTION_FIELDS, args.dry_run
    )

    if not args.dry_run:
        ensure_link_to_documents(cfg, extractions_id, args.dry_run)
        ensure_fields_on_table(cfg, cfg["documents_table_id"], OWNCLOUD_ACTIVE_FIELDS, args.dry_run)

    if args.seed_prompts and not args.dry_run:
        seed_prompt_records(cfg, prompts_id, args.dry_run)

    audit = api_permission_audit(cfg)
    report_path = args.report or (
        REPO_ROOT / "workspace/ocr_pipeline/09_logs/teable-api-permissions-audit.json"
    )
    if not args.dry_run:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"PromptTemplates table: {prompts_id}")
    print(f"DocExtractions table: {extractions_id}")
    print(f"OwnCloud table: {cfg['documents_table_id']}")
    print(f"Base: {cfg['base_id']}")
    if not args.dry_run:
        print(f"API audit: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
