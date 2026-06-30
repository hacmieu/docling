"""Per-doc-type key_fields schemas for structured metadata extraction."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from workspace.ocr_pipeline.metadata_normalize import normalize_doc_type

SCHEMAS_PATH = Path(__file__).resolve().parent / "config" / "metadata_schemas_vi.json"


@lru_cache(maxsize=1)
def load_metadata_schemas() -> dict[str, Any]:
    return json.loads(SCHEMAS_PATH.read_text(encoding="utf-8"))


def schema_for_doc_type(doc_type: str | None) -> dict[str, list[str]]:
    schemas = load_metadata_schemas()
    slug, _ = normalize_doc_type(doc_type)
    if slug and slug in schemas:
        entry = schemas[slug]
        return {
            "required": list(entry.get("required", [])),
            "optional": list(entry.get("optional", [])),
        }
    default = schemas.get("default", {})
    return {
        "required": list(default.get("required", ["ten", "so", "ngay", "don_vi"])),
        "optional": list(default.get("optional", [])),
    }


def field_list_text(fields: list[str]) -> str:
    if not fields:
        return "(không)"
    return ", ".join(fields)
