"""Source types, priority scores, and effective-metadata resolution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

SOURCE_PRIORITY: dict[str, int] = {
    "human_verified": 100,
    "human_webchat": 95,
    "google_vision": 70,
    "deepseek_cleanup": 50,
    "local_llm_ocr": 30,
}

SOURCE_LABELS_VI: dict[str, str] = {
    "human_verified": "Người xác nhận",
    "human_webchat": "Người (Webchat AI)",
    "google_vision": "Google Vision",
    "deepseek_cleanup": "DeepSeek làm sạch OCR",
    "local_llm_ocr": "OCR local (EasyOCR)",
}

# Ordered from highest to lowest — used for explicit fallback walk.
PRIORITY_ORDER: tuple[str, ...] = tuple(
    sorted(SOURCE_PRIORITY, key=lambda k: SOURCE_PRIORITY[k], reverse=True)
)

EXCLUDED_FROM_FALLBACK = frozenset({"archived", "superseded"})


@dataclass(frozen=True)
class ExtractionCandidate:
    extraction_id: int
    document_id: int
    source_type: str
    priority_score: int
    version_status: str
    category: str | None
    doc_type: str | None
    tags: list[str]
    extracted_summary: str | None
    raw_text: str | None


def priority_for(source_type: str) -> int:
    return SOURCE_PRIORITY.get(source_type, 0)


def is_eligible_for_fallback(version_status: str) -> bool:
    return version_status not in EXCLUDED_FROM_FALLBACK


def resolve_effective_extraction(
    candidates: Sequence[ExtractionCandidate],
) -> ExtractionCandidate | None:
    """Pick best metadata by priority waterfall, not by version_status=active alone.

    1. Filter out archived/superseded.
    2. Sort by priority_score DESC, then updated order in input (caller should pass newest first).
    3. Return the highest-priority row that exists — if no human row, fall back to
       google_vision, then deepseek_cleanup, then local_llm_ocr.
    """
    eligible = [c for c in candidates if is_eligible_for_fallback(c.version_status)]
    if not eligible:
        return None
    return max(eligible, key=lambda c: (c.priority_score, c.extraction_id))


def resolve_by_source_waterfall(
    candidates: Sequence[ExtractionCandidate],
) -> ExtractionCandidate | None:
    """Explicit tier walk: try human_verified, then human_webchat, … down to local_llm_ocr."""
    by_source: dict[str, list[ExtractionCandidate]] = {}
    for candidate in candidates:
        if not is_eligible_for_fallback(candidate.version_status):
            continue
        by_source.setdefault(candidate.source_type, []).append(candidate)
    for source_type in PRIORITY_ORDER:
        rows = by_source.get(source_type)
        if rows:
            return max(rows, key=lambda c: c.extraction_id)
    return None


def effective_metadata_sql() -> str:
    """Postgres: one effective extraction row per document (priority waterfall)."""
    return """
        SELECT DISTINCT ON (e.document_id)
            e.document_id,
            e.id AS extraction_id,
            e.source_type,
            e.priority_score,
            e.version_status,
            e.category,
            e.doc_type,
            e.tags,
            e.extracted_summary,
            e.raw_text
        FROM document_extractions e
        WHERE e.version_status NOT IN ('archived', 'superseded')
        ORDER BY e.document_id, e.priority_score DESC, e.updated_at DESC, e.id DESC
    """
