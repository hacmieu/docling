#!/usr/bin/env python3
"""Web app to browse OCR catalog stored in PostgreSQL."""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from datetime import date, datetime
from decimal import Decimal
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from socket import socket
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse
from uuid import UUID

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workspace.ocr_pipeline.concept_search import (
    build_search_sql,
    resolve_concept,
    snippet_around,
)
from workspace.ocr_pipeline.db_postgres import connect, database_url, load_dotenv
from workspace.ocr_pipeline.llm_context_pack import search_context_pack
from workspace.ocr_pipeline.search_qa import answer_from_search_items, synthesize_from_context_pack
from workspace.ocr_pipeline.teable_catalog import DRIVE_PREFIX_DEFAULT
from workspace.ocr_pipeline.teable_read import (
    catalog_stats as teable_catalog_stats,
    get_document as teable_get_document,
    is_teable_configured,
    list_documents as teable_list_documents,
    list_extractions_for_doc,
    public_config as teable_public_config,
)


def json_default(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Unsupported type: {type(value)}")


def serialize_row(row: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in row.items():
        if value is None:
            out[key] = None
        elif isinstance(value, (dict, list)):
            out[key] = value
        elif isinstance(value, (datetime, date, Decimal, UUID)):
            out[key] = json_default(value)
        else:
            out[key] = value
    return out


def display_path(path: str | None) -> str | None:
    if not path:
        return path
    return unicodedata.normalize("NFC", unquote(path))


class PgCatalogDb:
    def stats(self) -> dict[str, Any]:
        with connect() as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS success,
                    SUM(CASE WHEN status = 'cataloged' THEN 1 ELSE 0 END) AS cataloged,
                    SUM(CASE WHEN status = 'failure' THEN 1 ELSE 0 END) AS failure,
                    AVG(LENGTH(markdown)) AS avg_markdown_len,
                    SUM(CASE WHEN ai_review_status = 'success' THEN 1 ELSE 0 END) AS ai_reviewed,
                    SUM(
                        CASE WHEN owncloud_path LIKE 'project/hth-shared-drive%' THEN 1 ELSE 0 END
                    ) AS hth_shared,
                    SUM(
                        CASE WHEN owncloud_path LIKE '/Yen%' THEN 1 ELSE 0 END
                    ) AS legacy_yen,
                    SUM(
                        CASE
                            WHEN owncloud_path ILIKE '%.DS_Store' THEN 1
                            ELSE 0
                        END
                    ) AS dotfiles
                FROM documents
                """
            ).fetchone()
        return {
            "total": int(row[0] or 0),
            "success": int(row[1] or 0),
            "cataloged": int(row[2] or 0),
            "failure": int(row[3] or 0),
            "avg_markdown_len": float(row[4] or 0),
            "ai_reviewed": int(row[5] or 0),
            "hth_shared": int(row[6] or 0),
            "legacy_yen": int(row[7] or 0),
            "dotfiles": int(row[8] or 0),
        }

    def list_documents(
        self,
        limit: int,
        offset: int,
        status: str | None,
        query: str | None,
        drive: str | None,
        exclude_hidden: bool = True,
    ) -> tuple[list[dict[str, Any]], int]:
        filters: list[str] = []
        params: list[Any] = []
        if status:
            filters.append("status = %s")
            params.append(status)
        if query:
            filters.append(
                "(owncloud_path ILIKE %s OR source_path ILIKE %s OR local_path ILIKE %s)"
            )
            pattern = f"%{query}%"
            params.extend([pattern, pattern, pattern])
        if drive:
            filters.append("owncloud_path LIKE %s")
            params.append(f"{drive}%")
        if exclude_hidden:
            filters.append("owncloud_path NOT ILIKE %s")
            params.append("%.DS_Store")
        where = f"WHERE {' AND '.join(filters)}" if filters else ""

        count_sql = f"SELECT COUNT(*) FROM documents {where}"
        list_sql = f"""
            SELECT
                id,
                owncloud_path,
                source_path,
                status,
                created_at,
                updated_at,
                LENGTH(markdown) AS markdown_len,
                source_sha256,
                ai_review_status,
                ai_category,
                ai_doc_type,
                ai_ocr_quality
            FROM documents
            {where}
            ORDER BY updated_at DESC NULLS LAST, id DESC
            LIMIT %s OFFSET %s
        """
        with connect() as conn:
            total = int(conn.execute(count_sql, params).fetchone()[0])
            rows = conn.execute(list_sql, [*params, limit, offset]).fetchall()
        items = []
        for row in rows:
            items.append(
                {
                    "id": row[0],
                    "owncloud_path": display_path(row[1]),
                    "source_path": display_path(row[2]),
                    "status": row[3],
                    "created_at": row[4],
                    "updated_at": row[5],
                    "markdown_len": row[6],
                    "source_sha256": row[7],
                    "ai_review_status": row[8],
                    "ai_category": row[9],
                    "ai_doc_type": row[10],
                    "ai_ocr_quality": row[11],
                }
            )
        return items, total

    def get_document(self, doc_id: int) -> dict[str, Any] | None:
        with connect() as conn:
            row = conn.execute(
                """
                SELECT
                    id, owncloud_path, local_path, source_path, source_sha256,
                    status, error_message, created_at, updated_at,
                    markdown, doc_json,
                    ai_review, ai_review_status, ai_review_at, ai_review_model, ai_review_error,
                    ai_doc_type, ai_category, ai_tags, ai_key_fields, ai_ocr_quality,
                    verified_metadata, verified_at, verified_source
                FROM documents
                WHERE id = %s
                """,
                (doc_id,),
            ).fetchone()
        if row is None:
            return None
        columns = [
            "id",
            "owncloud_path",
            "local_path",
            "source_path",
            "source_sha256",
            "status",
            "error_message",
            "created_at",
            "updated_at",
            "markdown",
            "doc_json",
            "ai_review",
            "ai_review_status",
            "ai_review_at",
            "ai_review_model",
            "ai_review_error",
            "ai_doc_type",
            "ai_category",
            "ai_tags",
            "ai_key_fields",
            "ai_ocr_quality",
            "verified_metadata",
            "verified_at",
            "verified_source",
        ]
        doc = dict(zip(columns, row, strict=True))
        doc["owncloud_path"] = display_path(doc.get("owncloud_path"))
        doc["source_path"] = display_path(doc.get("source_path"))
        doc["local_path"] = display_path(doc.get("local_path"))
        return serialize_row(doc)

    def search_documents(
        self,
        query: str,
        limit: int,
        drive: str | None,
        phong_ban: str | None,
    ) -> dict[str, Any]:
        concept = resolve_concept(query)
        drive_prefix = drive or DRIVE_PREFIX_DEFAULT
        sql, params = build_search_sql(concept, drive_prefix, phong_ban, limit)
        with connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        items: list[dict[str, Any]] = []
        needle = concept.synonyms[0] if concept.synonyms else query
        for row in rows:
            (
                doc_id,
                owncloud_path,
                effective_source,
                effective_priority,
                category,
                doc_type,
                tags,
                summary,
                markdown_head,
            ) = row
            snippet = snippet_around(markdown_head or "", needle)
            items.append(
                {
                    "id": doc_id,
                    "owncloud_path": display_path(owncloud_path),
                    "effective_source": effective_source,
                    "effective_priority": effective_priority,
                    "category": category,
                    "doc_type": doc_type,
                    "tags": tags,
                    "summary": summary,
                    "snippet": snippet,
                }
            )
        return {
            "query": query,
            "concept_id": concept.concept_id,
            "synonyms": list(concept.synonyms),
            "items": items,
            "total": len(items),
        }

    def search_qa(
        self,
        query: str,
        limit: int,
        drive: str | None,
        phong_ban: str | None,
    ) -> dict[str, Any]:
        search_limit = max(1, min(limit, 10))
        search = self.search_documents(query, search_limit, drive, phong_ban)
        if not search["items"]:
            return {
                **search,
                "answer": "Không tìm thấy tài liệu phù hợp trong catalog đã lọc.",
                "reference_doc_ids": [],
                "model": None,
            }
        qa = answer_from_search_items(query, search["items"])
        return {**search, **qa}

    def search_context(
        self,
        mode: str,
        query: str,
        *,
        phong_ban: str | None,
        limit: int,
        all_catalog: bool,
    ) -> dict[str, Any]:
        pack = search_context_pack(
            mode,
            query,
            phong_ban=phong_ban,
            limit=limit,
            all_catalog=all_catalog,
        )
        return pack

    def synthesize_context(
        self,
        question: str,
        context_block: str,
        doc_count: int,
    ) -> dict[str, Any]:
        return synthesize_from_context_pack(question, context_block, doc_count=doc_count)


def is_port_available(host: str, port: int) -> bool:
    with socket() as sock:
        sock.settimeout(0.3)
        return sock.connect_ex((host, port)) != 0


def build_handler(db: PgCatalogDb, static_dir: Path):
    class Handler(BaseHTTPRequestHandler):
        def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
            body = json.dumps(payload, ensure_ascii=False, default=json_default).encode(
                "utf-8"
            )
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_file(self, path: Path, content_type: str) -> None:
            content = path.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)

            if parsed.path in ("/", "/index.html"):
                self._send_file(static_dir / "catalog.html", "text/html; charset=utf-8")
                return

            if parsed.path in ("/search", "/search.html"):
                self._send_file(static_dir / "search.html", "text/html; charset=utf-8")
                return

            if parsed.path in ("/teable", "/teable.html"):
                self._send_file(static_dir / "teable.html", "text/html; charset=utf-8")
                return

            if parsed.path == "/api/health":
                self._send_json({"ok": True, "database": database_url().split("@")[-1]})
                return

            if parsed.path == "/api/stats":
                self._send_json({"ok": True, "stats": db.stats()})
                return

            if parsed.path == "/api/teable/config":
                if not is_teable_configured():
                    self._send_json(
                        {
                            "ok": False,
                            "configured": False,
                            "error": "Thiếu TEABLE_* trong .env",
                        }
                    )
                    return
                try:
                    self._send_json(
                        {"ok": True, "configured": True, **teable_public_config()}
                    )
                except Exception as exc:
                    self._send_json({"ok": False, "error": str(exc)}, 502)
                return

            if parsed.path == "/api/teable/stats":
                if not is_teable_configured():
                    self._send_json({"ok": False, "error": "Teable chưa cấu hình"}, 503)
                    return
                try:
                    stats = teable_catalog_stats()
                except Exception as exc:
                    self._send_json({"ok": False, "error": str(exc)}, 502)
                    return
                self._send_json({"ok": True, "stats": stats, "source": "teable"})
                return

            if parsed.path == "/api/teable/documents":
                if not is_teable_configured():
                    self._send_json({"ok": False, "error": "Teable chưa cấu hình"}, 503)
                    return
                qs = parse_qs(parsed.query)
                limit = max(1, min(int(qs.get("limit", ["50"])[0]), 200))
                offset = max(0, int(qs.get("offset", ["0"])[0]))
                query = qs.get("q", [None])[0]
                phong_ban = qs.get("phong_ban", [None])[0]
                teable_status = qs.get("teable_status", [None])[0]
                exclude_hidden = qs.get("exclude_hidden", ["1"])[0] not in (
                    "0",
                    "false",
                    "no",
                )
                try:
                    items, total = teable_list_documents(
                        limit=limit,
                        offset=offset,
                        query=query,
                        phong_ban=phong_ban,
                        teable_status=teable_status,
                        exclude_hidden=exclude_hidden,
                    )
                except Exception as exc:
                    self._send_json({"ok": False, "error": str(exc)}, 502)
                    return
                self._send_json(
                    {
                        "ok": True,
                        "items": items,
                        "total": total,
                        "limit": limit,
                        "offset": offset,
                        "source": "teable",
                    }
                )
                return

            if parsed.path.startswith("/api/teable/documents/"):
                if not is_teable_configured():
                    self._send_json({"ok": False, "error": "Teable chưa cấu hình"}, 503)
                    return
                record_id = parsed.path.rsplit("/", 1)[1]
                try:
                    item = teable_get_document(record_id)
                except Exception as exc:
                    self._send_json({"ok": False, "error": str(exc)}, 502)
                    return
                if not item:
                    self._send_json({"ok": False, "error": "not found"}, 404)
                    return
                doc_id = item.get("doc_id")
                extractions: list[dict[str, Any]] = []
                if doc_id is not None:
                    try:
                        extractions = list_extractions_for_doc(int(doc_id))
                    except (TypeError, ValueError):
                        extractions = []
                self._send_json(
                    {
                        "ok": True,
                        "item": item,
                        "extractions": extractions,
                        "source": "teable",
                    }
                )
                return

            if parsed.path == "/api/search":
                qs = parse_qs(parsed.query)
                q = (qs.get("q", [""])[0] or "").strip()
                if not q:
                    self._send_json({"ok": False, "error": "q required"}, 400)
                    return
                limit = max(1, min(int(qs.get("limit", ["20"])[0]), 100))
                drive = qs.get("drive", [None])[0]
                phong_ban = qs.get("phong_ban", [None])[0]
                result = db.search_documents(q, limit, drive, phong_ban)
                self._send_json({"ok": True, **result})
                return

            if parsed.path == "/api/search/qa":
                qs = parse_qs(parsed.query)
                q = (qs.get("q", [""])[0] or "").strip()
                if not q:
                    self._send_json({"ok": False, "error": "q required"}, 400)
                    return
                limit = max(1, min(int(qs.get("limit", ["10"])[0]), 10))
                drive = qs.get("drive", [None])[0]
                phong_ban = qs.get("phong_ban", [None])[0]
                try:
                    result = db.search_qa(q, limit, drive, phong_ban)
                except Exception as exc:
                    self._send_json({"ok": False, "error": str(exc)}, 502)
                    return
                self._send_json({"ok": True, **result})
                return

            if parsed.path == "/api/search/context":
                qs = parse_qs(parsed.query)
                mode = (qs.get("mode", ["staff"])[0] or "staff").strip()
                q = (qs.get("q", [""])[0] or "").strip()
                if mode == "staff" and not q:
                    self._send_json({"ok": False, "error": "q required for staff mode"}, 400)
                    return
                limit = max(1, min(int(qs.get("limit", ["50"])[0]), 200))
                phong_ban = qs.get("phong_ban", [None])[0]
                all_catalog = qs.get("all_catalog", ["0"])[0] in ("1", "true", "yes")
                try:
                    pack = db.search_context(
                        mode,
                        q,
                        phong_ban=phong_ban,
                        limit=limit,
                        all_catalog=all_catalog,
                    )
                except ValueError as exc:
                    self._send_json({"ok": False, "error": str(exc)}, 400)
                    return
                self._send_json({"ok": True, **pack})
                return

            if parsed.path == "/api/documents":
                qs = parse_qs(parsed.query)
                limit = max(1, min(int(qs.get("limit", ["50"])[0]), 500))
                offset = max(0, int(qs.get("offset", ["0"])[0]))
                status = qs.get("status", [None])[0]
                query = qs.get("q", [None])[0]
                drive = qs.get("drive", [None])[0]
                exclude_hidden = qs.get("exclude_hidden", ["1"])[0] not in (
                    "0",
                    "false",
                    "no",
                )
                items, total = db.list_documents(
                    limit=limit,
                    offset=offset,
                    status=status,
                    query=query,
                    drive=drive,
                    exclude_hidden=exclude_hidden,
                )
                self._send_json(
                    {
                        "ok": True,
                        "items": [serialize_row(item) for item in items],
                        "total": total,
                        "limit": limit,
                        "offset": offset,
                    }
                )
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

        def do_POST(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path != "/api/search/synthesize":
                self._send_json({"ok": False, "error": "not found"}, 404)
                return
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length > 0 else b"{}"
            try:
                body = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError:
                self._send_json({"ok": False, "error": "invalid JSON body"}, 400)
                return
            question = str(body.get("question", "")).strip()
            context_block = str(body.get("llm_prompt_block", "")).strip()
            doc_count = int(body.get("doc_count", 0))
            if not question:
                self._send_json({"ok": False, "error": "question required"}, 400)
                return
            if not context_block:
                self._send_json({"ok": False, "error": "llm_prompt_block required"}, 400)
                return
            try:
                result = db.synthesize_context(question, context_block, doc_count)
            except ValueError as exc:
                self._send_json({"ok": False, "error": str(exc)}, 400)
                return
            except Exception as exc:
                self._send_json({"ok": False, "error": str(exc)}, 502)
                return
            self._send_json({"ok": True, **result})

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
            return

    return Handler


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument(
        "--check-port-only",
        action="store_true",
        help="Only check whether host:port is available and exit.",
    )
    return parser.parse_args()


def main() -> int:
    load_dotenv()
    args = parse_args()
    static_dir = Path(__file__).resolve().parent / "static"

    if not is_port_available(args.host, args.port):
        print(f"Port already in use: {args.host}:{args.port}")
        return 1
    print(f"Port available: {args.host}:{args.port}")
    if args.check_port_only:
        return 0

    db = PgCatalogDb()
    with connect() as conn:
        conn.execute("SELECT 1")

    handler = build_handler(db, static_dir)
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"Serving PostgreSQL catalog at http://{args.host}:{args.port}")
    print(f"Database: {database_url().split('@')[-1]}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
