#!/usr/bin/env python3
"""MVP ingest: read a folder, convert with Docling, store into SQLite."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

SUPPORTED_SUFFIXES = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".tif",
    ".tiff",
    ".docx",
    ".pptx",
    ".xlsx",
    ".html",
    ".htm",
    ".md",
    ".txt",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir",
        type=Path,
        required=True,
        help="Directory containing documents to ingest.",
    )
    parser.add_argument(
        "--sqlite-db",
        type=Path,
        default=Path("scratch/memory_tmp.db"),
        help="SQLite database path (default: scratch/memory_tmp.db).",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Include nested subdirectories.",
    )
    parser.add_argument(
        "--enable-ocr",
        action="store_true",
        help="Enable OCR for PDF conversion.",
    )
    parser.add_argument(
        "--force-full-page-ocr",
        action="store_true",
        help="Force full-page OCR (useful for scanned PDFs; slower).",
    )
    return parser.parse_args()


def collect_candidates(input_dir: Path, recursive: bool) -> list[Path]:
    walker = input_dir.rglob("*") if recursive else input_dir.glob("*")
    files = [path for path in walker if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES]
    return sorted(files)


def sha256sum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_path TEXT NOT NULL UNIQUE,
            source_sha256 TEXT NOT NULL,
            markdown TEXT NOT NULL,
            doc_json TEXT NOT NULL,
            status TEXT NOT NULL,
            error_message TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )


def build_converter(enable_ocr: bool, force_full_page_ocr: bool):
    from docling.document_converter import DocumentConverter

    if not enable_ocr:
        return DocumentConverter()

    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import (
        PdfPipelineOptions,
        TesseractCliOcrOptions,
    )
    from docling.document_converter import PdfFormatOption

    pdf_options = PdfPipelineOptions()
    pdf_options.do_ocr = True
    pdf_options.ocr_options = TesseractCliOcrOptions(
        force_full_page_ocr=force_full_page_ocr
    )
    return DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pdf_options)}
    )


def upsert_success(
    conn: sqlite3.Connection,
    source_path: Path,
    source_sha256: str,
    markdown: str,
    doc_json: str,
    now_iso: str,
) -> None:
    conn.execute(
        """
        INSERT INTO documents (
            source_path, source_sha256, markdown, doc_json, status, error_message, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, 'success', NULL, ?, ?)
        ON CONFLICT(source_path) DO UPDATE SET
            source_sha256=excluded.source_sha256,
            markdown=excluded.markdown,
            doc_json=excluded.doc_json,
            status='success',
            error_message=NULL,
            updated_at=excluded.updated_at
        """,
        (str(source_path), source_sha256, markdown, doc_json, now_iso, now_iso),
    )


def upsert_failure(
    conn: sqlite3.Connection,
    source_path: Path,
    source_sha256: str,
    error_message: str,
    now_iso: str,
) -> None:
    conn.execute(
        """
        INSERT INTO documents (
            source_path, source_sha256, markdown, doc_json, status, error_message, created_at, updated_at
        )
        VALUES (?, ?, '', '{}', 'failure', ?, ?, ?)
        ON CONFLICT(source_path) DO UPDATE SET
            source_sha256=excluded.source_sha256,
            status='failure',
            error_message=excluded.error_message,
            updated_at=excluded.updated_at
        """,
        (str(source_path), source_sha256, error_message, now_iso, now_iso),
    )


def main() -> int:
    args = parse_args()
    input_dir = args.input_dir.resolve()
    db_path = args.sqlite_db.resolve()

    if not input_dir.exists() or not input_dir.is_dir():
        print(f"Input directory not found: {input_dir}")
        return 1

    db_path.parent.mkdir(parents=True, exist_ok=True)
    files = collect_candidates(input_dir, recursive=args.recursive)
    if not files:
        print(f"No supported files found in: {input_dir}")
        return 0

    converter = build_converter(
        enable_ocr=args.enable_ocr,
        force_full_page_ocr=args.force_full_page_ocr,
    )
    conn = sqlite3.connect(db_path)
    init_db(conn)

    success = 0
    failure = 0

    for file_path in files:
        now_iso = datetime.now(UTC).isoformat()
        file_hash = sha256sum(file_path)
        try:
            result = converter.convert(file_path)
            markdown = result.document.export_to_markdown()
            doc_json = json.dumps(result.document.export_to_dict(), ensure_ascii=False)
            upsert_success(conn, file_path, file_hash, markdown, doc_json, now_iso)
            success += 1
            print(f"[OK] {file_path}")
        except Exception as exc:  # pragma: no cover - MVP failure capture
            upsert_failure(conn, file_path, file_hash, str(exc), now_iso)
            failure += 1
            print(f"[FAIL] {file_path}: {exc}")

    conn.commit()
    conn.close()

    print(
        f"Completed. total={len(files)} success={success} failure={failure} db={db_path}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
