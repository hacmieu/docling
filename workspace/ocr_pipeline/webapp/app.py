#!/usr/bin/env python3
"""Lightweight web app to browse OCR SQLite records."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from socket import socket
from typing import Any
from urllib.parse import parse_qs, urlparse

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workspace.ocr_pipeline.ocr_schema import ensure_documents_schema


def default_db_path() -> Path:
    sqlite_dir = Path(__file__).resolve().parent.parent / "08_sqlite"
    active_db = sqlite_dir / "ACTIVE_DB.txt"
    if active_db.exists():
        selected = active_db.read_text(encoding="utf-8").strip()
        if selected:
            return sqlite_dir / selected
    return sqlite_dir / "memory_tmp_vie_easyocr.db"


def is_port_available(host: str, port: int) -> bool:
    with socket() as sock:
        sock.settimeout(0.3)
        return sock.connect_ex((host, port)) != 0


class OcrDb:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def stats(self) -> dict[str, Any]:
        with self._connect() as conn:
            ensure_documents_schema(conn)
            row = conn.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS success,
                    SUM(CASE WHEN status = 'failure' THEN 1 ELSE 0 END) AS failure,
                    AVG(LENGTH(markdown)) AS avg_markdown_len,
                    SUM(CASE WHEN ai_review_status = 'success' THEN 1 ELSE 0 END) AS ai_reviewed
                FROM documents
                """
            ).fetchone()
        return {
            "total": int(row["total"] or 0),
            "success": int(row["success"] or 0),
            "failure": int(row["failure"] or 0),
            "avg_markdown_len": float(row["avg_markdown_len"] or 0),
            "ai_reviewed": int(row["ai_reviewed"] or 0),
        }

    def list_documents(
        self, limit: int, offset: int, status: str | None, query: str | None
    ) -> list[dict[str, Any]]:
        filters = []
        params: list[Any] = []
        if status:
            filters.append("status = ?")
            params.append(status)
        if query:
            filters.append("source_path LIKE ?")
            params.append(f"%{query}%")
        where = f"WHERE {' AND '.join(filters)}" if filters else ""
        sql = f"""
            SELECT
                id,
                source_path,
                status,
                created_at,
                updated_at,
                LENGTH(markdown) AS markdown_len,
                source_sha256,
                ai_review_status
            FROM documents
            {where}
            ORDER BY updated_at DESC, id DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]

    def get_document(self, doc_id: int) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    id, source_path, source_sha256, status, error_message,
                    created_at, updated_at, markdown, doc_json,
                    ai_review, ai_review_status, ai_review_at, ai_review_model, ai_review_error
                FROM documents
                WHERE id = ?
                """,
                (doc_id,),
            ).fetchone()
        return dict(row) if row else None


def build_handler(db: OcrDb, static_dir: Path):
    class Handler(BaseHTTPRequestHandler):
        def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_index(self) -> None:
            index_path = static_dir / "index.html"
            content = index_path.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)

            if parsed.path in ("/", "/index.html"):
                self._send_index()
                return

            if parsed.path == "/api/health":
                self._send_json({"ok": True, "db": str(db.db_path)})
                return

            if parsed.path == "/api/stats":
                self._send_json({"ok": True, "stats": db.stats()})
                return

            if parsed.path == "/api/documents":
                qs = parse_qs(parsed.query)
                limit = max(1, min(int(qs.get("limit", ["20"])[0]), 200))
                offset = max(0, int(qs.get("offset", ["0"])[0]))
                status = qs.get("status", [None])[0]
                query = qs.get("q", [None])[0]
                docs = db.list_documents(
                    limit=limit, offset=offset, status=status, query=query
                )
                self._send_json({"ok": True, "items": docs})
                return

            if parsed.path.startswith("/api/documents/"):
                try:
                    doc_id = int(parsed.path.rsplit("/", 1)[1])
                except ValueError:
                    self._send_json({"ok": False, "error": "invalid document id"}, 400)
                    return
                doc = db.get_document(doc_id)
                if not doc:
                    self._send_json({"ok": False, "error": "not found"}, 404)
                    return
                self._send_json({"ok": True, "item": doc})
                return

            self._send_json({"ok": False, "error": "not found"}, 404)

    return Handler


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--db-path", type=Path, default=default_db_path())
    parser.add_argument(
        "--check-port-only",
        action="store_true",
        help="Only check whether host:port is available and exit.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    db_path = args.db_path.resolve()
    static_dir = Path(__file__).resolve().parent / "static"

    if not db_path.exists():
        print(f"DB not found: {db_path}")
        return 1
    if not is_port_available(args.host, args.port):
        print(f"Port already in use: {args.host}:{args.port}")
        return 1
    print(f"Port available: {args.host}:{args.port}")
    if args.check_port_only:
        return 0

    db = OcrDb(db_path)
    with db._connect() as conn:
        ensure_documents_schema(conn)
        conn.commit()
    handler = build_handler(db, static_dir)
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"Serving SQLite webapp at http://{args.host}:{args.port}")
    print(f"Using DB: {db_path}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
