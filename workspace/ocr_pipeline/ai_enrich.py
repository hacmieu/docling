"""Shared AI enrichment (category, tags, summary) for any OCR lane."""

from __future__ import annotations

import json
import time
from typing import Any, Literal

import requests

from workspace.ocr_pipeline.metadata_normalize import (
    normalize_category,
    normalize_doc_type,
    normalize_tags,
)
from workspace.ocr_pipeline.pipeline_config import PipelineConfig, load_pipeline_config

Lane = Literal["raw", "vision"]

ENRICH_PROMPT = """Bạn là chuyên gia phân loại tài liệu hành chính/pháp lý tiếng Việt.

Phân tích markdown OCR và trả về ĐÚNG một JSON object (không bọc ```), schema:
{{
  "doc_type": "string",
  "category": "string",
  "tags": ["tag1", "tag2"],
  "key_fields": {{"ten": "...", "so": "...", "ngay": "...", "don_vi": "..."}},
  "ocr_quality": "tot|kha|yeu",
  "review_vi": "đoạn tóm tắt ngắn bằng tiếng Việt"
}}

Tên file: {filename}

--- OCR MARKDOWN ---
{markdown}
"""


def enrich_api_config(lane: Lane, config: PipelineConfig | None = None) -> dict[str, str]:
    cfg = config or load_pipeline_config()
    model = cfg.raw_enrich_model if lane == "raw" else cfg.vision_enrich_model
    if not cfg.enrich_api_key:
        raise RuntimeError("PIPELINE_ENRICH_API_KEY or AI_BOX_API_KEY missing in .env")
    return {"key": cfg.enrich_api_key, "url": cfg.enrich_api_url.rstrip("/"), "model": model}


def call_ai_enrich(
    ocr_text: str,
    filename: str,
    api_cfg: dict[str, str],
    *,
    max_chars: int = 12000,
) -> dict[str, object]:
    prompt = ENRICH_PROMPT.format(
        filename=filename,
        markdown=ocr_text[:max_chars],
    )
    endpoint = f"{api_cfg['url']}/v1/chat/completions"
    payload = {
        "model": api_cfg["model"],
        "messages": [
            {"role": "system", "content": "Trả về JSON hợp lệ duy nhất, không thêm text ngoài JSON."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }
    headers = {"Authorization": f"Bearer {api_cfg['key']}", "Content-Type": "application/json"}
    for attempt in range(5):
        response = requests.post(endpoint, headers=headers, json=payload, timeout=120)
        if response.status_code == 429:
            time.sleep(min(60, 5 * (2**attempt)))
            continue
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return json.loads(content)
    raise RuntimeError("AI enrich API rate limited")


def apply_enrichment_to_extraction(
    conn: Any,
    extraction_id: int,
    data: dict[str, object],
    model_name: str,
) -> None:
    tags = [str(t) for t in data.get("tags", []) if str(t).strip()]
    cat_slug, cat_label = normalize_category(str(data.get("category", "")))
    type_slug, _ = normalize_doc_type(str(data.get("doc_type", "")))
    norm_tags = normalize_tags(tags)
    conn.execute(
        """
        UPDATE document_extractions SET
            category = %s,
            doc_type = %s,
            tags = %s::jsonb,
            key_fields = %s::jsonb,
            extracted_summary = %s,
            model_name = %s,
            version_status = 'active',
            updated_at = NOW()
        WHERE id = %s
        """,
        (
            cat_label or str(data.get("category", "")),
            type_slug or str(data.get("doc_type", "")),
            json.dumps(norm_tags, ensure_ascii=False),
            json.dumps(data.get("key_fields", {}), ensure_ascii=False),
            str(data.get("review_vi", "")),
            model_name,
            extraction_id,
        ),
    )


def enrich_extraction_from_ocr_text(
    conn: Any,
    extraction_id: int,
    ocr_text: str,
    filename: str,
    lane: Lane,
    config: PipelineConfig | None = None,
) -> dict[str, object]:
    """Run text enrich on OCR output and persist ai_* fields on the extraction row."""
    cfg = config or load_pipeline_config()
    api_cfg = enrich_api_config(lane, cfg)
    data = call_ai_enrich(ocr_text, filename, api_cfg, max_chars=cfg.enrich_max_chars)
    apply_enrichment_to_extraction(conn, extraction_id, data, api_cfg["model"])
    return data
