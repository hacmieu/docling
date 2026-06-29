"""Normalize category, doc_type, and tags for catalog + Teable sync."""

from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any

TAXONOMY_PATH = Path(__file__).resolve().parent / "config" / "taxonomy_vi.json"


def slugify(value: str) -> str:
    text = unicodedata.normalize("NFC", value.strip().lower())
    decomposed = unicodedata.normalize("NFD", text)
    without_marks = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    collapsed = re.sub(r"[^a-z0-9]+", "-", without_marks)
    return collapsed.strip("-")


@lru_cache(maxsize=1)
def load_taxonomy() -> dict[str, Any]:
    return json.loads(TAXONOMY_PATH.read_text(encoding="utf-8"))


def _alias_index(section: str) -> dict[str, str]:
    taxonomy = load_taxonomy()
    index: dict[str, str] = {}
    for slug, entry in taxonomy.get(section, {}).items():
        index[slugify(slug)] = slug
        index[slugify(entry.get("label", slug))] = slug
        for alias in entry.get("aliases", []):
            index[slugify(alias)] = slug
    return index


def normalize_category(raw: str | None) -> tuple[str | None, str | None]:
    """Return (slug, display label)."""
    if not raw or not str(raw).strip():
        return None, None
    key = slugify(str(raw))
    slug = _alias_index("categories").get(key)
    if slug:
        label = load_taxonomy()["categories"][slug]["label"]
        return slug, label
    slug = key
    label = str(raw).strip()
    if label.islower() or label.isupper():
        label = label[:1].upper() + label[1:]
    return slug, label


def normalize_doc_type(raw: str | None) -> tuple[str | None, str | None]:
    """Return (slug, display label). Slug is canonical storage for Teable select."""
    if not raw or not str(raw).strip():
        return None, None
    key = slugify(str(raw))
    slug = _alias_index("doc_types").get(key)
    if slug:
        label = load_taxonomy()["doc_types"][slug]["label"]
        return slug, label
    return key, load_taxonomy()["doc_types"].get(key, {}).get("label", key.replace("-", " ").title())


def normalize_tag(raw: str) -> str:
    text = str(raw).strip()
    if not text:
        return ""
    key = slugify(text)
    tag_aliases = load_taxonomy().get("tag_aliases", {})
    for slug, aliases in tag_aliases.items():
        if key == slugify(slug):
            return slug
        for alias in aliases:
            if key == slugify(alias):
                return slug
    return key


def normalize_tags(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        parts = [p.strip() for p in re.split(r"[,;]", raw) if p.strip()]
    elif isinstance(raw, list):
        parts = [str(p).strip() for p in raw if str(p).strip()]
    else:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for part in parts:
        slug = normalize_tag(part)
        if slug and slug not in seen:
            seen.add(slug)
            out.append(slug)
    return sorted(out)


def collect_taxonomy_choices() -> dict[str, list[str]]:
    taxonomy = load_taxonomy()
    categories = [entry["label"] for entry in taxonomy.get("categories", {}).values()]
    doc_types = list(taxonomy.get("doc_types", {}).keys())
    tags = sorted(taxonomy.get("tag_aliases", {}).keys())
    return {
        "ai_category": sorted(set(categories)),
        "ai_doc_type": sorted(set(doc_types)),
        "ai_tags": tags,
    }


def merge_discovered_choices(
    categories: list[str | None],
    doc_types: list[str | None],
    tag_lists: list[list[str]],
) -> dict[str, list[str]]:
    base = collect_taxonomy_choices()
    cat_labels: set[str] = set(base["ai_category"])
    doc_slugs: set[str] = set(base["ai_doc_type"])
    tag_slugs: set[str] = set(base["ai_tags"])
    for raw in categories:
        _slug, label = normalize_category(raw)
        if label:
            cat_labels.add(label)
    for raw in doc_types:
        slug, _label = normalize_doc_type(raw)
        if slug:
            doc_slugs.add(slug)
    for tags in tag_lists:
        for tag in normalize_tags(tags):
            tag_slugs.add(tag)
    return {
        "ai_category": sorted(cat_labels),
        "ai_doc_type": sorted(doc_slugs),
        "ai_tags": sorted(tag_slugs),
    }
