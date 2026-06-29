"""Concept-based staff search over documents + effective extractions."""

from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

CONCEPTS_PATH = Path(__file__).resolve().parent / "config" / "concepts_vi.json"
SNIPPET_LEN = 400


@dataclass(frozen=True)
class ConceptQuery:
    concept_id: str | None
    raw_query: str
    synonyms: tuple[str, ...]
    tag_slugs: tuple[str, ...]
    categories: tuple[str, ...]


@lru_cache(maxsize=1)
def load_concepts() -> dict[str, Any]:
    return json.loads(CONCEPTS_PATH.read_text(encoding="utf-8"))


def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text.strip())


def resolve_concept(query: str) -> ConceptQuery:
    q = _nfc(query)
    q_lower = q.lower()
    concepts = load_concepts()
    for concept_id, entry in concepts.items():
        synonyms = [_nfc(s) for s in entry.get("synonyms", [])]
        if q_lower == concept_id.replace("-", " ") or q in synonyms or q_lower in [s.lower() for s in synonyms]:
            return ConceptQuery(
                concept_id=concept_id,
                raw_query=q,
                synonyms=tuple(synonyms) if synonyms else (q,),
                tag_slugs=tuple(entry.get("tags", [])),
                categories=tuple(entry.get("categories", [])),
            )
    return ConceptQuery(
        concept_id=None,
        raw_query=q,
        synonyms=(q,),
        tag_slugs=(),
        categories=(),
    )


def snippet_around(text: str, needle: str, radius: int = SNIPPET_LEN // 2) -> str:
    if not text or not needle:
        return (text or "")[:SNIPPET_LEN]
    hay = _nfc(text)
    pin = _nfc(needle)
    idx = hay.lower().find(pin.lower())
    if idx < 0:
        return hay[:SNIPPET_LEN]
    start = max(0, idx - radius)
    end = min(len(hay), idx + len(pin) + radius)
    excerpt = hay[start:end]
    if start > 0:
        excerpt = "…" + excerpt
    if end < len(hay):
        excerpt = excerpt + "…"
    return excerpt


def build_search_sql(
    concept: ConceptQuery,
    drive_prefix: str,
    phong_ban: str | None,
    limit: int,
) -> tuple[str, list[Any]]:
    patterns = list(dict.fromkeys(concept.synonyms))
    text_checks = " OR ".join(["d.markdown ILIKE %s" for _ in patterns])

    tag_clause = ""
    if concept.tag_slugs:
        tag_checks = " OR ".join(["e.tags::text ILIKE %s" for _ in concept.tag_slugs])
        tag_clause = f"OR ({tag_checks})"

    cat_clause = ""
    if concept.categories:
        cat_checks = " OR ".join(["e.category ILIKE %s" for _ in concept.categories])
        cat_clause = f"OR ({cat_checks})"

    phong_clause = ""
    if phong_ban:
        phong_clause = "AND d.owncloud_path ILIKE %s"

    sql = f"""
        SELECT
            d.id,
            d.owncloud_path,
            d.effective_source_type,
            d.effective_priority,
            e.category,
            e.doc_type,
            e.tags,
            e.extracted_summary,
            left(d.markdown, 5000) AS markdown_head
        FROM documents d
        LEFT JOIN effective_document_extractions e ON e.document_id = d.id
        WHERE d.owncloud_path LIKE %s
          {phong_clause}
          AND (
            {text_checks}
            {tag_clause}
            {cat_clause}
          )
        ORDER BY d.effective_priority DESC NULLS LAST, d.updated_at DESC
        LIMIT %s
    """
    params: list[Any] = [f"{drive_prefix}%"]
    if phong_ban:
        params.append(f"%{phong_ban}%")
    params.extend([f"%{p}%" for p in patterns])
    if concept.tag_slugs:
        params.extend([f"%{t}%" for t in concept.tag_slugs])
    if concept.categories:
        params.extend([f"%{c}%" for c in concept.categories])
    params.append(limit)
    return sql, params
