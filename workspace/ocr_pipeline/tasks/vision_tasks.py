"""Gemini vision OCR tasks (image-only; separate API key)."""

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

from workspace.ocr_pipeline.celery_app import app
from workspace.ocr_pipeline.db_postgres import connect, load_dotenv
from workspace.ocr_pipeline.extraction_priority import SOURCE_PRIORITY

REPO_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = REPO_ROOT / ".env"
VISION_PROMPT = (
    "OCR toàn bộ văn bản tiếng Việt trong ảnh. Trả về plain text, giữ xuống dòng hợp lý. "
    "Không thêm giải thích."
)


def vision_api_config() -> dict[str, str]:
    load_dotenv(ENV_FILE)
    key = os.environ.get("AI_BOX_VISION_API_KEY", "").strip()
    url = os.environ.get("AI_BOX_API_URL", "https://api.ai-box.vn").rstrip("/")
    model = os.environ.get("AI_BOX_VISION_MODEL", "gemini-3-flash").strip()
    if not key:
        raise RuntimeError("AI_BOX_VISION_API_KEY missing in .env")
    return {"key": key, "url": url, "model": model}


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


def call_vision_ocr(image_bytes: bytes, mime: str, cfg: dict[str, str]) -> str:
    b64 = base64.standard_b64encode(image_bytes).decode("ascii")
    endpoint = f"{cfg['url']}/v1/chat/completions"
    payload = {
        "model": cfg["model"],
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": VISION_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{b64}"},
                    },
                ],
            }
        ],
        "temperature": 0.0,
    }
    headers = {"Authorization": f"Bearer {cfg['key']}", "Content-Type": "application/json"}
    rate_limit = os.environ.get("CELERY_VISION_RATE_LIMIT", "10/m")
    _ = rate_limit  # enforced via Celery task decorator
    for attempt in range(6):
        response = requests.post(endpoint, headers=headers, json=payload, timeout=180)
        if response.status_code == 429:
            time.sleep(min(90, 5 * (2**attempt)))
            continue
        response.raise_for_status()
        return str(response.json()["choices"][0]["message"]["content"]).strip()
    raise RuntimeError("Vision API rate limited after retries")


def next_version_no(conn: Any, document_id: int) -> int:
    row = conn.execute(
        "SELECT COALESCE(MAX(version_no), 0) + 1 FROM document_extractions WHERE document_id = %s",
        (document_id,),
    ).fetchone()
    return int(row[0])


def persist_vision_extraction(
    document_id: int,
    raw_text: str,
    model_name: str,
    local_path: str,
) -> int:
    with connect() as conn:
        version_no = next_version_no(conn, document_id)
        row = conn.execute(
            """
            INSERT INTO document_extractions (
                document_id, version_no, source_type, priority_score, version_status,
                raw_text, extracted_summary, model_name, created_by, key_fields
            ) VALUES (%s, %s, 'google_vision', %s, 'draft', %s, %s, %s, %s, %s::jsonb)
            RETURNING id
            """,
            (
                document_id,
                version_no,
                SOURCE_PRIORITY["google_vision"],
                raw_text,
                "Gemini vision OCR (page 1)",
                model_name,
                "celery:vision_tasks",
                json.dumps({"local_path": local_path, "page": 1}),
            ),
        ).fetchone()
        return int(row[0])


@app.task(
    name="workspace.ocr_pipeline.tasks.vision_tasks.vision_ocr_document",
    bind=True,
    rate_limit=os.environ.get("CELERY_VISION_RATE_LIMIT", "10/m"),
    max_retries=5,
    default_retry_delay=30,
)
def vision_ocr_document(self, document_id: int) -> dict[str, Any]:
    """Run Gemini vision OCR on first page / image file for one catalog document."""
    started = datetime.now(UTC).isoformat()
    with connect() as conn:
        row = conn.execute(
            "SELECT id, local_path, owncloud_path FROM documents WHERE id = %s",
            (document_id,),
        ).fetchone()
    if not row:
        return {"ok": False, "document_id": document_id, "error": "not found"}
    _doc_id, local_path, owncloud_path = row
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
    try:
        image_bytes, mime = _image_bytes_for_path(path)
        cfg = vision_api_config()
        text = call_vision_ocr(image_bytes, mime, cfg)
        extraction_id = persist_vision_extraction(document_id, text, cfg["model"], str(path))
        return {
            "ok": True,
            "document_id": document_id,
            "extraction_id": extraction_id,
            "text_len": len(text),
            "started_at": started,
            "finished_at": datetime.now(UTC).isoformat(),
        }
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 429:
            raise self.retry(exc=exc) from exc
        return {"ok": False, "document_id": document_id, "error": str(exc)}
    except Exception as exc:
        return {"ok": False, "document_id": document_id, "error": str(exc)}
