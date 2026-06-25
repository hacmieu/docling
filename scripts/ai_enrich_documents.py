#!/usr/bin/env python3
"""AI enrichment: review OCR text and persist tags/category/structured metadata."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workspace.ocr_pipeline.db_postgres import connect, link_document_tags, load_dotenv

ENV_FILE = REPO_ROOT / ".env"
MAX_MARKDOWN_CHARS = 12000

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--doc-id", type=int, default=None)
    parser.add_argument("--sleep-seconds", type=float, default=4.0)
    return parser.parse_args()


def api_config() -> dict[str, str]:
    load_dotenv(ENV_FILE)
    key = os.environ.get("AI_BOX_API_KEY", "").strip()
    url = os.environ.get("AI_BOX_API_URL", "https://api.ai-box.vn").rstrip("/")
    model = os.environ.get("AI_BOX_MODEL", "deepseek-v4-pro").strip()
    if not key:
        raise RuntimeError("AI_BOX_API_KEY missing in .env")
    return {"key": key, "url": url, "model": model}


def call_ai_enrich(markdown: str, filename: str, cfg: dict[str, str]) -> dict[str, object]:
    prompt = ENRICH_PROMPT.format(
        filename=filename,
        markdown=markdown[:MAX_MARKDOWN_CHARS],
    )
    endpoint = f"{cfg['url']}/v1/chat/completions"
    payload = {
        "model": cfg["model"],
        "messages": [
            {"role": "system", "content": "Trả về JSON hợp lệ duy nhất, không thêm text ngoài JSON."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }
    headers = {"Authorization": f"Bearer {cfg['key']}", "Content-Type": "application/json"}
    for attempt in range(5):
        response = requests.post(endpoint, headers=headers, json=payload, timeout=120)
        if response.status_code == 429:
            time.sleep(min(60, 5 * (2**attempt)))
            continue
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return json.loads(content)
    raise RuntimeError("AI API rate limited")


def main() -> int:
    args = parse_args()
    cfg = api_config()
    processed = success = failure = skipped = 0

    with connect() as conn:
        if args.doc_id is not None:
            rows = conn.execute(
                """
                SELECT id, owncloud_path, source_path, markdown, ai_review_status
                FROM documents WHERE id = %s AND status IN ('success', 'cataloged')
                """,
                (args.doc_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, owncloud_path, source_path, markdown, ai_review_status
                FROM documents
                WHERE status IN ('success', 'cataloged')
                ORDER BY id
                """
            ).fetchall()

        for doc_id, owncloud_path, source_path, markdown, review_status in rows:
            if args.limit and processed >= args.limit:
                break
            if review_status == "success" and not args.force:
                skipped += 1
                continue

            filename = Path(owncloud_path or source_path or "unknown").name
            now = datetime.now(UTC)
            processed += 1
            print(f"[AI] id={doc_id} file={filename}")
            try:
                data = call_ai_enrich(markdown or "", filename, cfg)
                tags = [str(t) for t in data.get("tags", []) if str(t).strip()]
                conn.execute(
                    """
                    UPDATE documents SET
                        ai_review = %s,
                        ai_review_status = 'success',
                        ai_review_at = %s,
                        ai_review_model = %s,
                        ai_review_error = NULL,
                        ai_doc_type = %s,
                        ai_category = %s,
                        ai_tags = %s::jsonb,
                        ai_key_fields = %s::jsonb,
                        ai_ocr_quality = %s,
                        updated_at = %s
                    WHERE id = %s
                    """,
                    (
                        str(data.get("review_vi", "")),
                        now,
                        cfg["model"],
                        str(data.get("doc_type", "")),
                        str(data.get("category", "")),
                        json.dumps(tags, ensure_ascii=False),
                        json.dumps(data.get("key_fields", {}), ensure_ascii=False),
                        str(data.get("ocr_quality", "")),
                        now,
                        doc_id,
                    ),
                )
                link_document_tags(conn, doc_id, tags)
                success += 1
                print(f"[OK] id={doc_id}")
            except Exception as exc:
                conn.execute(
                    """
                    UPDATE documents SET
                        ai_review_status = 'failure',
                        ai_review_at = %s,
                        ai_review_model = %s,
                        ai_review_error = %s,
                        updated_at = %s
                    WHERE id = %s
                    """,
                    (now, cfg["model"], str(exc), now, doc_id),
                )
                failure += 1
                print(f"[FAIL] id={doc_id}: {exc}")

            if args.sleep_seconds > 0:
                time.sleep(args.sleep_seconds)

    print(
        f"Completed enrich. processed={processed} success={success} "
        f"failure={failure} skipped={skipped}"
    )
    return 0 if failure == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
