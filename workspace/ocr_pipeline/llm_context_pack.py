"""Build compact, token-estimated context packs for LLM from catalog metadata."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import unquote

from workspace.ocr_pipeline.db_postgres import connect


def estimate_tokens(text: str) -> int:
    """Rough token count (≈4 chars/token for Vietnamese + JSON)."""
    return max(1, len(text) // 4)


def path_tail(owncloud_path: str | None) -> str:
    if not owncloud_path:
        return ""
    decoded = unquote(owncloud_path.replace("+", " "))
    parts = decoded.replace("\\", "/").split("/")
    return "/".join(parts[-3:]) if len(parts) >= 3 else decoded


@dataclass(frozen=True)
class StaffSearchFilter:
    name: str
    phong_ban: str | None = None


@dataclass(frozen=True)
class DocTypeSearchFilter:
    doc_types: tuple[str, ...]
    path_contains: str | None = None
    phong_ban: str | None = None


def _row_to_doc_item(row: tuple[Any, ...]) -> dict[str, Any]:
    doc_id, owncloud_path, doc_type, category, tags, key_fields, summary, source = row
    return {
        "doc_id": doc_id,
        "doc_type": doc_type,
        "category": category,
        "tags": tags,
        "key_fields": key_fields or {},
        "summary": (summary or "").strip(),
        "path_tail": path_tail(owncloud_path),
        "effective_source": source,
    }


def _name_patterns(name: str) -> list[str]:
    base = name.strip()
    patterns = [f"%{base}%"]
    if "ể" in base or "Ể" in base:
        patterns.append(f"%{base.replace('ể', 'ề').replace('Ể', 'Ề')}%")
    if "ề" in base or "Ề" in base:
        patterns.append(f"%{base.replace('ề', 'ể').replace('Ề', 'Ể')}%")
    return list(dict.fromkeys(patterns))


_STAFF_SUBFOLDERS = ("HSCN", "VB,", "VB%2C", "Hồ sơ", "CCCD")


def _staff_folder_prefix(owncloud_path: str) -> str | None:
    """Path prefix up to staff name folder (handles URL-encoded OC paths)."""
    path = owncloud_path.replace("\\", "/")
    for marker in _STAFF_SUBFOLDERS:
        idx = path.upper().find(marker.upper())
        if idx > 0:
            return path[: path.rfind("/", 0, idx)]
    parts = path.split("/")
    if len(parts) >= 2:
        return "/".join(parts[:-2])
    return None


def search_staff_documents(
    name: str,
    *,
    phong_ban: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Find documents by key_fields name, summary, and staff folder path."""
    patterns = _name_patterns(name)
    field_checks: list[str] = []
    params: list[Any] = []
    for pat in patterns:
        field_checks.extend(
            [
                "e.key_fields->>'ten' ILIKE %s",
                "e.key_fields->>'ho_ten' ILIKE %s",
                "e.extracted_summary ILIKE %s",
            ]
        )
        params.extend([pat, pat, pat])
    extra = ""
    if phong_ban:
        extra = " AND d.owncloud_path ILIKE %s"
        params.append(f"%{phong_ban}%")
    where = " OR ".join(field_checks)
    sql = f"""
        SELECT d.id, d.owncloud_path, e.doc_type, e.category, e.tags,
               e.key_fields, e.extracted_summary, d.effective_source_type
        FROM documents d
        JOIN effective_document_extractions e ON e.document_id = d.id
        WHERE d.status IN ('success', 'cataloged')
          AND ({where}){extra}
        ORDER BY d.id
        LIMIT %s
    """
    params.append(limit)
    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    items = [_row_to_doc_item(r) for r in rows]

    # Include sibling docs under the same staff folder prefix.
    folder_prefixes: set[str] = set()
    with connect() as conn:
        for item in items:
            row = conn.execute(
                "SELECT owncloud_path FROM documents WHERE id = %s",
                (item["doc_id"],),
            ).fetchone()
            if row and row[0]:
                prefix = _staff_folder_prefix(str(row[0]))
                if prefix:
                    folder_prefixes.add(prefix)
        seen_ids = {int(i["doc_id"]) for i in items}
        for prefix in folder_prefixes:
            sibs = conn.execute(
                """
                SELECT d.id, d.owncloud_path, e.doc_type, e.category, e.tags,
                       e.key_fields, e.extracted_summary, d.effective_source_type
                FROM documents d
                JOIN effective_document_extractions e ON e.document_id = d.id
                WHERE d.status IN ('success', 'cataloged')
                  AND d.owncloud_path LIKE %s
                ORDER BY d.id
                """,
                (f"{prefix}%",),
            ).fetchall()
            for row in sibs:
                if int(row[0]) not in seen_ids:
                    items.append(_row_to_doc_item(row))
                    seen_ids.add(int(row[0]))
    items.sort(key=lambda x: int(x["doc_id"]))
    return items


def search_by_doc_types(
    doc_types: list[str],
    *,
    path_contains: str | None = None,
    phong_ban: str | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    type_clauses = " OR ".join(["e.doc_type = %s" for _ in doc_types])
    type_clauses += " OR " + " OR ".join(["e.doc_type LIKE %s" for _ in doc_types])
    params: list[Any] = list(doc_types) + [f"{t}%" for t in doc_types]
    extra = ""
    if path_contains:
        # Path stored URL-encoded; also match decoded folder names in summary.
        extra += " AND (d.owncloud_path ILIKE %s OR e.extracted_summary ILIKE %s)"
        params.extend([f"%{path_contains}%", f"%{path_contains}%"])
    if phong_ban:
        extra += " AND d.owncloud_path ILIKE %s"
        params.append(f"%{phong_ban}%")
    sql = f"""
        SELECT d.id, d.owncloud_path, e.doc_type, e.category, e.tags,
               e.key_fields, e.extracted_summary, d.effective_source_type
        FROM documents d
        JOIN effective_document_extractions e ON e.document_id = d.id
        WHERE d.status IN ('success', 'cataloged')
          AND ({type_clauses}){extra}
        ORDER BY e.doc_type, d.id
        LIMIT %s
    """
    params.append(limit)
    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_row_to_doc_item(r) for r in rows]


def build_llm_context_pack(
    query: str,
    documents: list[dict[str, Any]],
    *,
    filter_meta: dict[str, Any] | None = None,
    include_summaries: bool = True,
) -> dict[str, Any]:
    """Compact JSON bundle suitable for LLM input + token budgeting."""
    slim_docs: list[dict[str, Any]] = []
    for doc in documents:
        entry: dict[str, Any] = {
            "doc_id": doc["doc_id"],
            "doc_type": doc.get("doc_type"),
            "key_fields": doc.get("key_fields") or {},
            "path_tail": doc.get("path_tail"),
        }
        if include_summaries and doc.get("summary"):
            entry["summary"] = doc["summary"][:500]
        slim_docs.append(entry)

    payload = {
        "query": query,
        "filter": filter_meta or {},
        "doc_count": len(slim_docs),
        "documents": slim_docs,
    }
    json_text = json.dumps(payload, ensure_ascii=False, indent=2)
    chars = len(json_text)
    prompt_block = format_llm_prompt_block(query, slim_docs)
    return {
        **payload,
        "chars": chars,
        "prompt_chars": len(prompt_block),
        "estimated_tokens_json": estimate_tokens(json_text),
        "estimated_tokens_prompt": estimate_tokens(prompt_block),
        "llm_prompt_block": prompt_block,
    }


def format_llm_prompt_block(query: str, documents: list[dict[str, Any]]) -> str:
    lines = [f"Câu hỏi: {query}", f"Số tài liệu: {len(documents)}", ""]
    for doc in documents:
        kf = doc.get("key_fields") or {}
        kf_short = json.dumps(kf, ensure_ascii=False)
        summary = doc.get("summary", "")
        block = (
            f"[doc_id={doc['doc_id']}] type={doc.get('doc_type')} "
            f"path=.../{doc.get('path_tail', '')}\n"
            f"key_fields={kf_short}\n"
        )
        if summary:
            block += f"summary={summary[:400]}\n"
        lines.append(block)
    return "\n".join(lines)
