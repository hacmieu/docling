"""Read-only Teable catalog access for the web UI."""

from __future__ import annotations

import os
from typing import Any

import requests

from workspace.ocr_pipeline.db_postgres import load_dotenv
from workspace.ocr_pipeline.teable_catalog import (
    ENV_FILE,
    display_path,
    teable_config,
    teable_headers,
)

LIST_MAX_SCAN = 5000
PAGE_SIZE = 200


def teable_full_config() -> dict[str, str]:
    load_dotenv(ENV_FILE)
    cfg = teable_config()
    extractions_id = os.environ.get("TEABLE_TABLE_EXTRACTIONS_ID", "").strip()
    if not extractions_id:
        raise RuntimeError("TEABLE_TABLE_EXTRACTIONS_ID required in .env")
    api_url = cfg["url"]
    app_url = os.environ.get("TEABLE_APP_URL", "").strip()
    if not app_url:
        app_url = api_url.removesuffix("/api").rstrip("/") or api_url
    base_id = os.environ.get("TEABLE_BASE_ID", "").strip()
    cfg["extractions_table_id"] = extractions_id
    cfg["app_url"] = app_url
    cfg["base_id"] = base_id
    return cfg


def is_teable_configured() -> bool:
    load_dotenv(ENV_FILE)
    url = os.environ.get("TEABLE_API_URL", "").strip()
    token = os.environ.get("TEABLE_API_TOKEN", "").strip()
    docs = os.environ.get("TEABLE_TABLE_DOCUMENTS_ID", "").strip()
    ext = os.environ.get("TEABLE_TABLE_EXTRACTIONS_ID", "").strip()
    return bool(url and token and docs and ext)


def _record_endpoint(cfg: dict[str, str], table_id: str) -> str:
    return f"{cfg['url']}/table/{table_id}/record"


def fetch_records_page(
    cfg: dict[str, str],
    table_id: str,
    *,
    skip: int = 0,
    take: int = PAGE_SIZE,
) -> tuple[list[dict[str, Any]], int | None]:
    response = requests.get(
        _record_endpoint(cfg, table_id),
        headers=teable_headers(cfg["token"]),
        params={"fieldKeyType": "name", "take": take, "skip": skip},
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    records = payload.get("records") or []
    total = payload.get("total")
    if total is not None:
        try:
            total = int(total)
        except (TypeError, ValueError):
            total = None
    return records, total


def fetch_record(cfg: dict[str, str], table_id: str, record_id: str) -> dict[str, Any] | None:
    endpoint = f"{_record_endpoint(cfg, table_id)}/{record_id}"
    response = requests.get(
        endpoint,
        headers=teable_headers(cfg["token"]),
        params={"fieldKeyType": "name"},
        timeout=60,
    )
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


def normalize_document_record(record: dict[str, Any], cfg: dict[str, str]) -> dict[str, Any]:
    fields = record.get("fields") or {}
    path = display_path(str(fields.get("owncloud_path") or ""))
    return {
        "teable_id": str(record.get("id") or ""),
        "doc_id": fields.get(cfg["field_number"]) or fields.get("Number"),
        "label": fields.get(cfg["field_label"]) or fields.get("Label") or "",
        "teable_status": fields.get(cfg["field_status"]) or fields.get("Status") or "",
        "owncloud_path": path,
        "file_name": fields.get("file_name") or "",
        "phong_ban": fields.get("phong_ban") or "",
        "catalog_status": fields.get("catalog_status") or "",
        "markdown_preview": fields.get("markdown_preview") or "",
        "active_priority": fields.get("active_priority"),
        "active_source": fields.get("active_source") or "",
        "extraction_version_count": fields.get("extraction_version_count"),
        "updated_at": fields.get("updated_at") or "",
        "doc_extractions_link": fields.get("DocExtractions"),
    }


def normalize_extraction_record(record: dict[str, Any]) -> dict[str, Any]:
    fields = record.get("fields") or {}
    return {
        "teable_id": str(record.get("id") or ""),
        "postgres_extraction_id": fields.get("postgres_extraction_id"),
        "doc_id": fields.get("doc_id"),
        "version_label": fields.get("version_label") or "",
        "source_type": fields.get("source_type") or "",
        "priority": fields.get("priority"),
        "version_status": fields.get("version_status") or "",
        "ai_category": fields.get("ai_category") or fields.get("category") or "",
        "ai_doc_type": fields.get("ai_doc_type") or "",
        "ai_tags": fields.get("ai_tags") or "",
        "key_fields_json": fields.get("key_fields_json") or "",
        "extracted_summary": fields.get("extracted_summary") or "",
        "raw_text_preview": fields.get("raw_text_preview") or "",
        "model_name": fields.get("model_name") or "",
        "enrich_model": fields.get("enrich_model") or "",
        "created_at": fields.get("created_at") or "",
        "document_link": fields.get("document"),
    }


def _matches_document_filters(
    item: dict[str, Any],
    *,
    query: str | None,
    phong_ban: str | None,
    teable_status: str | None,
    exclude_hidden: bool,
) -> bool:
    path = (item.get("owncloud_path") or "").lower()
    if exclude_hidden and (".ds_store" in path or path.endswith("/.ds_store")):
        return False
    if teable_status and item.get("teable_status") != teable_status:
        return False
    if phong_ban:
        pb = (item.get("phong_ban") or "").lower()
        if phong_ban.lower() not in pb:
            return False
    if query:
        q = query.lower()
        hay = " ".join(
            [
                str(item.get("label") or ""),
                str(item.get("file_name") or ""),
                str(item.get("owncloud_path") or ""),
                str(item.get("doc_id") or ""),
                str(item.get("phong_ban") or ""),
            ]
        ).lower()
        if q not in hay:
            return False
    return True


def _scan_documents(
    cfg: dict[str, str],
    *,
    query: str | None,
    phong_ban: str | None,
    teable_status: str | None,
    exclude_hidden: bool,
    limit: int,
    offset: int,
) -> tuple[list[dict[str, Any]], int]:
    matched: list[dict[str, Any]] = []
    skip = 0
    scanned = 0
    total_known: int | None = None
    while scanned < LIST_MAX_SCAN:
        records, total_known = fetch_records_page(
            cfg, cfg["table_id"], skip=skip, take=PAGE_SIZE
        )
        if not records:
            break
        for record in records:
            scanned += 1
            item = normalize_document_record(record, cfg)
            if _matches_document_filters(
                item,
                query=query,
                phong_ban=phong_ban,
                teable_status=teable_status,
                exclude_hidden=exclude_hidden,
            ):
                matched.append(item)
        if len(records) < PAGE_SIZE:
            break
        skip += PAGE_SIZE
    total = len(matched)
    page = matched[offset : offset + limit]
    return page, total


def list_documents(
    *,
    limit: int = 50,
    offset: int = 0,
    query: str | None = None,
    phong_ban: str | None = None,
    teable_status: str | None = None,
    exclude_hidden: bool = True,
) -> tuple[list[dict[str, Any]], int]:
    cfg = teable_full_config()
    has_filter = bool(query or phong_ban or teable_status or not exclude_hidden)
    if has_filter:
        return _scan_documents(
            cfg,
            query=query,
            phong_ban=phong_ban,
            teable_status=teable_status,
            exclude_hidden=exclude_hidden,
            limit=limit,
            offset=offset,
        )
    records, total_known = fetch_records_page(
        cfg, cfg["table_id"], skip=offset, take=limit
    )
    items = [normalize_document_record(r, cfg) for r in records]
    if exclude_hidden:
        items = [
            i
            for i in items
            if ".ds_store" not in (i.get("owncloud_path") or "").lower()
        ]
    total = total_known if total_known is not None else offset + len(items)
    return items, total


def get_document(record_id: str) -> dict[str, Any] | None:
    cfg = teable_full_config()
    record = fetch_record(cfg, cfg["table_id"], record_id)
    if not record:
        return None
    return normalize_document_record(record, cfg)


def list_extractions_for_doc(
    doc_id: int,
    *,
    limit: int = 50,
) -> list[dict[str, Any]]:
    cfg = teable_full_config()
    matched: list[dict[str, Any]] = []
    skip = 0
    scanned = 0
    while scanned < LIST_MAX_SCAN and len(matched) < limit:
        records, _ = fetch_records_page(
            cfg, cfg["extractions_table_id"], skip=skip, take=PAGE_SIZE
        )
        if not records:
            break
        for record in records:
            scanned += 1
            item = normalize_extraction_record(record)
            try:
                row_doc_id = int(item.get("doc_id"))
            except (TypeError, ValueError):
                continue
            if row_doc_id == doc_id:
                matched.append(item)
                if len(matched) >= limit:
                    break
        if len(records) < PAGE_SIZE:
            break
        skip += PAGE_SIZE
    matched.sort(key=lambda x: (-(x.get("priority") or 0), x.get("version_label") or ""))
    return matched


def catalog_stats() -> dict[str, Any]:
    cfg = teable_full_config()
    doc_count = 0
    ext_count = 0
    skip = 0
    while skip < LIST_MAX_SCAN:
        records, total = fetch_records_page(cfg, cfg["table_id"], skip=skip, take=PAGE_SIZE)
        if not records:
            break
        doc_count += len(records)
        if total is not None:
            doc_count = total
            break
        if len(records) < PAGE_SIZE:
            break
        skip += PAGE_SIZE
    skip = 0
    while skip < LIST_MAX_SCAN:
        records, total = fetch_records_page(
            cfg, cfg["extractions_table_id"], skip=skip, take=PAGE_SIZE
        )
        if not records:
            break
        ext_count += len(records)
        if total is not None:
            ext_count = total
            break
        if len(records) < PAGE_SIZE:
            break
        skip += PAGE_SIZE
    return {"documents": doc_count, "extractions": ext_count}


def public_config() -> dict[str, str]:
    cfg = teable_full_config()
    return {
        "app_url": cfg["app_url"],
        "base_id": cfg.get("base_id") or "",
        "documents_table_id": cfg["table_id"],
        "extractions_table_id": cfg["extractions_table_id"],
    }
