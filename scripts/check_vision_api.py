#!/usr/bin/env python3
"""Validate Google Gemini vision configuration and image OCR access."""

from __future__ import annotations

import sys
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workspace.ocr_pipeline.db_postgres import load_dotenv
from workspace.ocr_pipeline.tasks.vision_tasks import vision_api_config


def main() -> int:
    load_dotenv()
    cfg = vision_api_config()
    text_key = __import__("os").environ.get("AI_BOX_API_KEY", "")
    vision_key = (
        __import__("os").environ.get("GOOGLE_API_KEY", "")
        or __import__("os").environ.get("GOOGLE_VISION_API_KEY", "")
    )
    print(f"vision_model={cfg['model']}")
    print(f"vision_key_distinct_from_text_key={vision_key != text_key}")
    # List models (sanity)
    models = requests.get(
        f"{cfg['url']}/models?key={cfg['key']}",
        timeout=30,
    )
    print(f"models_list_status={models.status_code}")
    if models.status_code == 200:
        raw_models = models.json().get("models", [])
        ids = [
            m.get("name", "").split("/")[-1]
            for m in raw_models
            if m.get("name")
        ]
        print(f"models_available={ids}")
    # Image probe (gemini is image-only)
    from workspace.ocr_pipeline.db_postgres import connect

    with connect() as conn:
        row = conn.execute(
            """
            SELECT local_path FROM documents
            WHERE local_path IS NOT NULL AND status = 'success'
            LIMIT 1
            """
        ).fetchone()
    if not row:
        print("SKIP image probe: no local_path in catalog")
        return 0
    from workspace.ocr_pipeline.tasks.vision_tasks import VISION_PROMPT, _image_bytes_for_path
    import base64

    image_bytes, mime = _image_bytes_for_path(Path(row[0]))
    b64 = base64.standard_b64encode(image_bytes).decode()
    endpoint = f"{cfg['url']}/models/{cfg['model']}:generateContent?key={cfg['key']}"
    response = requests.post(
        endpoint,
        headers={"Content-Type": "application/json"},
        json={
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": VISION_PROMPT},
                        {"inline_data": {"mime_type": mime, "data": b64}},
                    ],
                }
            ],
            "generationConfig": {"temperature": 0.0},
        },
        timeout=120,
    )
    print(f"image_probe_status={response.status_code}")
    if response.status_code == 200:
        parts = response.json().get("candidates", [{}])[0].get("content", {}).get("parts", [])
        text = "\n".join(str(p.get("text", "")) for p in parts if p.get("text"))
        print(f"OK: vision OCR works, sample_len={len(text)}")
        return 0
    print(response.text[:400])
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
