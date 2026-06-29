"""Teable catalog field definitions and API helpers."""

from __future__ import annotations

import json
import os
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import unquote

import requests

from workspace.ocr_pipeline.db_postgres import load_dotenv
from workspace.ocr_pipeline.metadata_normalize import (
    normalize_category,
    normalize_doc_type,
    normalize_tags,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = REPO_ROOT / ".env"
MARKDOWN_PREVIEW_LEN = 2000
DRIVE_PREFIX_DEFAULT = "project/hth-shared-drive"


@dataclass(frozen=True)
class CatalogFieldSpec:
    name: str
    field_type: str
    description: str = ""


# Fields beyond MVP Label / Number / Status
EXTENDED_CATALOG_FIELDS: tuple[CatalogFieldSpec, ...] = (
    CatalogFieldSpec("owncloud_path", "longText", "OCIS WebDAV path (NFC decoded)"),
    CatalogFieldSpec("file_name", "singleLineText", "File name from path"),
    CatalogFieldSpec("phong_ban", "singleLineText", "Department folder segment"),
    CatalogFieldSpec("catalog_status", "singleLineText", "Postgres documents.status"),
    CatalogFieldSpec("markdown_preview", "longText", "First 2000 chars of OCR markdown"),
    CatalogFieldSpec("ocr_duration_s", "number", "doc_json.ocr_sla.duration_seconds"),
    CatalogFieldSpec("ocr_started_at", "singleLineText", "ISO timestamp OCR batch start"),
    CatalogFieldSpec("ocr_finished_at", "singleLineText", "ISO timestamp OCR batch end"),
    CatalogFieldSpec("ai_category", "singleLineText", "AI category"),
    CatalogFieldSpec("ai_doc_type", "singleLineText", "AI doc_type slug"),
    CatalogFieldSpec("ai_tags", "longText", "AI tags comma-separated"),
    CatalogFieldSpec("ai_review", "longText", "AI Vietnamese summary"),
    CatalogFieldSpec("updated_at", "singleLineText", "Postgres updated_at ISO"),
)


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


def teable_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def display_path(path: str | None) -> str:
    if not path:
        return ""
    return unicodedata.normalize("NFC", unquote(path))


def parse_phong_ban(owncloud_path: str | None, drive_prefix: str = DRIVE_PREFIX_DEFAULT) -> str:
    path = display_path(owncloud_path)
    prefix = f"{drive_prefix}/"
    if not path.startswith(prefix):
        return ""
    rest = path[len(prefix) :]
    segment = rest.split("/", 1)[0] if rest else ""
    return segment


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


def tags_to_text(ai_tags: Any) -> str:
    """Legacy comma text; prefer normalize_tags for Teable multipleSelect."""
    slugs = normalize_tags(ai_tags)
    return ", ".join(slugs)


def tags_for_teable(ai_tags: Any) -> list[str]:
    return normalize_tags(ai_tags)


def ocr_sla(doc_json: Any) -> dict[str, Any]:
    if isinstance(doc_json, dict):
        sla = doc_json.get("ocr_sla")
        if isinstance(sla, dict):
            return sla
    return {}


def list_table_fields(cfg: dict[str, str]) -> list[dict[str, Any]]:
    endpoint = f"{cfg['url']}/table/{cfg['table_id']}/field"
    response = requests.get(endpoint, headers=teable_headers(cfg["token"]), timeout=60)
    response.raise_for_status()
    return response.json()


def create_table_field(cfg: dict[str, str], spec: CatalogFieldSpec) -> dict[str, Any]:
    endpoint = f"{cfg['url']}/table/{cfg['table_id']}/field"
    body: dict[str, Any] = {"name": spec.name, "type": spec.field_type}
    if spec.field_type == "number":
        body["options"] = {"formatting": {"type": "decimal", "precision": 2}}
    response = requests.post(
        endpoint,
        headers=teable_headers(cfg["token"]),
        json=body,
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def ensure_catalog_fields(cfg: dict[str, str], dry_run: bool = False) -> list[str]:
    """Create missing extended fields; return names created."""
    existing = {f["name"] for f in list_table_fields(cfg)}
    created: list[str] = []
    for spec in EXTENDED_CATALOG_FIELDS:
        if spec.name in existing:
            continue
        if dry_run:
            print(f"[DRY] CREATE FIELD {spec.name} ({spec.field_type})")
            created.append(spec.name)
            continue
        result = create_table_field(cfg, spec)
        print(f"[FIELD] created {spec.name} id={result.get('id')}")
        created.append(spec.name)
        existing.add(spec.name)
    return created


def build_record_fields(
    cfg: dict[str, str],
    row: tuple[Any, ...],
    drive_prefix: str = DRIVE_PREFIX_DEFAULT,
) -> dict[str, Any]:
    (
        doc_id,
        owncloud_path,
        status,
        ai_category,
        ai_review_status,
        ai_review,
        ai_doc_type,
        ai_tags,
        markdown,
        doc_json,
        updated_at,
    ) = row
    path = display_path(owncloud_path)
    sla = ocr_sla(doc_json)
    duration = sla.get("duration_seconds")
    _cat_slug, cat_label = normalize_category(ai_category)
    type_slug, _type_label = normalize_doc_type(ai_doc_type)
    norm_tags = tags_for_teable(ai_tags)
    fields: dict[str, Any] = {
        cfg["field_label"]: build_label(doc_id, owncloud_path, cat_label or ai_category),
        cfg["field_number"]: doc_id,
        cfg["field_status"]: map_teable_status(status or "", ai_review_status),
        "owncloud_path": path,
        "file_name": Path(path).name if path else "",
        "phong_ban": parse_phong_ban(owncloud_path, drive_prefix),
        "catalog_status": status or "",
        "markdown_preview": (markdown or "")[:MARKDOWN_PREVIEW_LEN],
        "ai_review": ai_review or "",
        "ocr_started_at": str(sla.get("started_at") or ""),
        "ocr_finished_at": str(sla.get("finished_at") or ""),
        "updated_at": updated_at.isoformat() if updated_at else "",
    }
    if cat_label:
        fields["ai_category"] = cat_label
    if type_slug:
        fields["ai_doc_type"] = type_slug
    if norm_tags:
        fields["ai_tags"] = norm_tags
    if duration is not None:
        try:
            fields["ocr_duration_s"] = float(duration)
        except (TypeError, ValueError):
            fields["ocr_duration_s"] = None
    return fields
