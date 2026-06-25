"""SQLite schema helpers for OCR pipeline documents table."""

from __future__ import annotations

import sqlite3

AI_REVIEW_COLUMNS: tuple[tuple[str, str], ...] = (
    ("ai_review", "TEXT"),
    ("ai_review_status", "TEXT"),
    ("ai_review_at", "TEXT"),
    ("ai_review_model", "TEXT"),
    ("ai_review_error", "TEXT"),
)


def existing_columns(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("PRAGMA table_info(documents)").fetchall()
    return {row[1] for row in rows}


def ensure_documents_schema(conn: sqlite3.Connection) -> None:
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
    present = existing_columns(conn)
    for name, col_type in AI_REVIEW_COLUMNS:
        if name not in present:
            conn.execute(f"ALTER TABLE documents ADD COLUMN {name} {col_type}")
