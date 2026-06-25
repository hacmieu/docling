#!/usr/bin/env python3
"""Run AI quality review on OCR markdown stored in SQLite."""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workspace.ocr_pipeline.ocr_schema import ensure_documents_schema

DEFAULT_DB = (
    REPO_ROOT / "workspace/ocr_pipeline/08_sqlite/memory_tmp_vie_easyocr_quality.db"
)
ACTIVE_DB_POINTER = REPO_ROOT / "workspace/ocr_pipeline/08_sqlite/ACTIVE_DB.txt"
ENV_FILE = REPO_ROOT / ".env"
MAX_MARKDOWN_CHARS = 12000

REVIEW_PROMPT = """Bạn là chuyên gia kiểm tra chất lượng OCR tài liệu tiếng Việt.

Phân tích nội dung markdown OCR bên dưới và trả lời bằng tiếng Việt, theo cấu trúc:
1. Loại tài liệu (ước đoán)
2. Các trường thông tin chính trích được (tên, số, ngày, đơn vị...)
3. Chất lượng OCR (tốt/khá/yếu) và lỗi điển hình (dấu, ký tự lạ, thiếu chữ)
4. Đề xuất cải thiện (nếu có)

Tên file gốc: {filename}

--- OCR MARKDOWN ---
{markdown}
"""


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def resolve_db_path(explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit.resolve()
    if ACTIVE_DB_POINTER.exists():
        selected = ACTIVE_DB_POINTER.read_text(encoding="utf-8").strip()
        if selected:
            return (ACTIVE_DB_POINTER.parent / selected).resolve()
    return DEFAULT_DB.resolve()


def api_config() -> dict[str, str]:
    load_dotenv(ENV_FILE)
    key = os.environ.get("AI_BOX_API_KEY", "").strip()
    url = os.environ.get("AI_BOX_API_URL", "https://api.ai-box.vn").rstrip("/")
    model = os.environ.get("AI_BOX_MODEL", "deepseek-v4-pro").strip()
    if not key:
        raise RuntimeError("AI_BOX_API_KEY is missing. Set it in .env")
    return {"key": key, "url": url, "model": model}


def call_ai_review(markdown: str, filename: str, cfg: dict[str, str]) -> str:
    prompt = REVIEW_PROMPT.format(
        filename=filename,
        markdown=markdown[:MAX_MARKDOWN_CHARS],
    )
    endpoint = f"{cfg['url']}/v1/chat/completions"
    payload = {
        "model": cfg["model"],
        "messages": [
            {
                "role": "system",
                "content": "Bạn kiểm tra chất lượng OCR và trích xuất thông tin chính xác.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }
    headers = {
        "Authorization": f"Bearer {cfg['key']}",
        "Content-Type": "application/json",
    }
    last_error: Exception | None = None
    for attempt in range(5):
        try:
            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=120,
            )
            if response.status_code == 429:
                wait_s = min(60, 5 * (2**attempt))
                time.sleep(wait_s)
                continue
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except requests.HTTPError as exc:
            last_error = exc
            if exc.response is not None and exc.response.status_code == 429:
                wait_s = min(60, 5 * (2**attempt))
                time.sleep(wait_s)
                continue
            raise
        except Exception as exc:
            last_error = exc
            raise
    raise RuntimeError(f"AI API rate limited after retries: {last_error}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sqlite-db",
        type=Path,
        default=None,
        help="SQLite DB path (default: ACTIVE_DB.txt pointer).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-run AI review even if ai_review_status is already success.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Max documents to process (0 = all pending).",
    )
    parser.add_argument(
        "--doc-id",
        type=int,
        default=None,
        help="Process only one document id.",
    )
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=4.0,
        help="Delay between API calls to reduce rate limiting (default: 4.0).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    db_path = resolve_db_path(args.sqlite_db)
    if not db_path.exists():
        print(f"DB not found: {db_path}")
        return 1

    cfg = api_config()
    conn = sqlite3.connect(db_path, timeout=60)
    conn.execute("PRAGMA busy_timeout = 60000")
    ensure_documents_schema(conn)

    if args.doc_id is not None:
        rows = conn.execute(
            """
            SELECT id, source_path, markdown, ai_review_status
            FROM documents
            WHERE id = ? AND status = 'success'
            """,
            (args.doc_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT id, source_path, markdown, ai_review_status
            FROM documents
            WHERE status = 'success'
            ORDER BY id ASC
            """
        ).fetchall()

    processed = 0
    success = 0
    failure = 0
    skipped = 0

    for doc_id, source_path, markdown, review_status in rows:
        if args.limit and processed >= args.limit:
            break
        if review_status == "success" and not args.force:
            skipped += 1
            continue

        filename = Path(source_path).name
        now_iso = datetime.now(UTC).isoformat()
        processed += 1
        print(f"[AI] doc_id={doc_id} file={filename}")
        try:
            review = call_ai_review(markdown or "", filename, cfg)
            conn.execute(
                """
                UPDATE documents
                SET ai_review = ?, ai_review_status = 'success',
                    ai_review_at = ?, ai_review_model = ?, ai_review_error = NULL
                WHERE id = ?
                """,
                (review, now_iso, cfg["model"], doc_id),
            )
            success += 1
            print(f"[OK] doc_id={doc_id}")
        except Exception as exc:
            conn.execute(
                """
                UPDATE documents
                SET ai_review_status = 'failure', ai_review_at = ?,
                    ai_review_model = ?, ai_review_error = ?
                WHERE id = ?
                """,
                (now_iso, cfg["model"], str(exc), doc_id),
            )
            failure += 1
            print(f"[FAIL] doc_id={doc_id}: {exc}")

        if args.sleep_seconds > 0:
            time.sleep(args.sleep_seconds)

    conn.commit()
    conn.close()
    print(
        "Completed AI review. "
        f"processed={processed} success={success} failure={failure} skipped={skipped} db={db_path}"
    )
    return 0 if failure == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
