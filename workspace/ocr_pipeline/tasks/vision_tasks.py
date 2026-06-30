"""Gemini vision OCR tasks via Google Generative Language API."""

from __future__ import annotations

import base64
import io
import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests

from workspace.ocr_pipeline.ai_enrich import enrich_extraction_from_ocr_text
from workspace.ocr_pipeline.celery_app import app
from workspace.ocr_pipeline.db_postgres import connect, load_dotenv
from workspace.ocr_pipeline.extraction_store import inherit_document_ai_metadata
from workspace.ocr_pipeline.pipeline_config import (
    PipelineConfig,
    load_pipeline_config,
    vision_api_key,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = REPO_ROOT / ".env"


def vision_api_config(config: PipelineConfig | None = None) -> dict[str, str]:
    load_dotenv(ENV_FILE)
    cfg = config or load_pipeline_config()
    key = vision_api_key(cfg)
    if not key:
        raise RuntimeError(
            f"Vision API key missing for provider={cfg.vision_provider} "
            "(GOOGLE_API_KEY or PIPELINE_VISION_API_KEY)"
        )
    return {"key": key, "url": cfg.vision_api_url.rstrip("/"), "model": cfg.vision_model}


def _image_bytes_for_path(path: Path) -> tuple[bytes, str]:
    suffix = path.suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"}:
        data = path.read_bytes()
        mime = "image/png" if suffix == ".png" else "image/jpeg"
        return data, mime
    if suffix == ".pdf":
        import pypdfium2 as pdfium

        doc = pdfium.PdfDocument(str(path))
        if len(doc) == 0:
            raise ValueError("PDF has no pages")
        page = doc[0]
        bitmap = page.render(scale=2)
        pil_image = bitmap.to_pil()
        buffer = io.BytesIO()
        pil_image.save(buffer, format="PNG")
        return buffer.getvalue(), "image/png"
    raise ValueError(f"Unsupported file type for vision OCR: {suffix}")


def call_vision_ocr(
    image_bytes: bytes,
    mime: str,
    cfg: dict[str, str],
    *,
    ocr_prompt: str,
) -> str:
    b64 = base64.standard_b64encode(image_bytes).decode("ascii")
    endpoint = f"{cfg['url']}/models/{cfg['model']}:generateContent?key={cfg['key']}"
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": ocr_prompt},
                    {"inline_data": {"mime_type": mime, "data": b64}},
                ],
            }
        ],
        "generationConfig": {"temperature": 0.0},
    }
    headers = {"Content-Type": "application/json"}
    rate_limit = os.environ.get("CELERY_VISION_RATE_LIMIT", "10/m")
    _ = rate_limit
    for attempt in range(6):
        response = requests.post(endpoint, headers=headers, json=payload, timeout=180)
        if response.status_code == 429:
            time.sleep(min(90, 5 * (2**attempt)))
            continue
        response.raise_for_status()
        data = response.json()
        candidates = data.get("candidates") or []
        if not candidates:
            return ""
        parts = candidates[0].get("content", {}).get("parts", [])
        texts = [str(part.get("text", "")) for part in parts if part.get("text")]
        return "\n".join(texts).strip()
    raise RuntimeError("Vision API rate limited after retries")


def next_version_no(conn: Any, document_id: int) -> int:
    row = conn.execute(
        "SELECT COALESCE(MAX(version_no), 0) + 1 FROM document_extractions WHERE document_id = %s",
        (document_id,),
    ).fetchone()
    return int(row[0])


def persist_vision_extraction(
    conn: Any,
    document_id: int,
    raw_text: str,
    model_name: str,
    local_path: str,
    config: PipelineConfig,
) -> int:
    version_no = next_version_no(conn, document_id)
    row = conn.execute(
        """
        INSERT INTO document_extractions (
            document_id, version_no, source_type, priority_score, version_status,
            raw_text, extracted_summary, model_name, created_by, key_fields
        ) VALUES (%s, %s, %s, %s, 'draft', %s, %s, %s, %s, %s::jsonb)
        RETURNING id
        """,
        (
            document_id,
            version_no,
            config.source_vision,
            config.vision_priority,
            raw_text,
            f"{config.vision_provider} vision OCR (page 1)",
            model_name,
            f"pipeline:vision:{config.vision_provider}",
            json.dumps(
                {"local_path": local_path, "page": 1, "provider": config.vision_provider},
                ensure_ascii=False,
            ),
        ),
    ).fetchone()
    return int(row[0])


def enrich_vision_extraction(
    conn: Any,
    document_id: int,
    extraction_id: int,
    raw_text: str,
    filename: str,
    config: PipelineConfig,
) -> str:
    """Lane 2: vision OCR text => AI refine (ai_* on extraction). Returns status token."""
    if not config.vision_enrich_enabled or not raw_text.strip():
        return "skipped"
    try:
        enrich_extraction_from_ocr_text(
            conn, extraction_id, raw_text, filename, "vision", config
        )
        return "enriched"
    except Exception:
        if config.vision_enrich_fallback_inherit:
            inherit_document_ai_metadata(conn, document_id, extraction_id)
            return "inherit_fallback"
        raise


@app.task(
    name="workspace.ocr_pipeline.tasks.vision_tasks.vision_ocr_document",
    bind=True,
    rate_limit=os.environ.get("CELERY_VISION_RATE_LIMIT", "10/m"),
    max_retries=5,
    default_retry_delay=30,
)
def vision_ocr_document(self, document_id: int) -> dict[str, Any]:
    """Vision OCR (lane 2) then AI enrich on vision text."""
    started = datetime.now(UTC).isoformat()
    pipeline = load_pipeline_config()
    with connect() as conn:
        row = conn.execute(
            "SELECT id, local_path, owncloud_path, source_path FROM documents WHERE id = %s",
            (document_id,),
        ).fetchone()
    if not row:
        return {"ok": False, "document_id": document_id, "error": "not found"}
    _doc_id, local_path, owncloud_path, source_path = row
    if not local_path:
        return {
            "ok": False,
            "document_id": document_id,
            "error": "local_path missing",
            "owncloud_path": owncloud_path,
        }
    path = Path(local_path)
    if not path.is_file():
        return {
            "ok": False,
            "document_id": document_id,
            "error": f"file not found: {path}",
        }
    filename = Path(owncloud_path or source_path or path.name).name
    try:
        image_bytes, mime = _image_bytes_for_path(path)
        vcfg = vision_api_config(pipeline)
        text = call_vision_ocr(
            image_bytes, mime, vcfg, ocr_prompt=pipeline.vision_ocr_prompt
        )
        enrich_status = "skipped"
        with connect() as conn:
            extraction_id = persist_vision_extraction(
                conn, document_id, text, vcfg["model"], str(path), pipeline
            )
            enrich_status = enrich_vision_extraction(
                conn, document_id, extraction_id, text, filename, pipeline
            )
        return {
            "ok": True,
            "document_id": document_id,
            "extraction_id": extraction_id,
            "text_len": len(text),
            "enrich_status": enrich_status,
            "vision_provider": pipeline.vision_provider,
            "vision_model": vcfg["model"],
            "enrich_model": pipeline.vision_enrich_model,
            "started_at": started,
            "finished_at": datetime.now(UTC).isoformat(),
        }
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 429:
            raise self.retry(exc=exc) from exc
        return {"ok": False, "document_id": document_id, "error": str(exc)}
    except Exception as exc:
        return {"ok": False, "document_id": document_id, "error": str(exc)}
