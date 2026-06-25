"""PostgreSQL helpers for OCR pipeline catalog."""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = REPO_ROOT / ".env"


def load_dotenv(path: Path = ENV_FILE) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def database_url() -> str:
    load_dotenv()
    return os.environ.get(
        "OCR_DATABASE_URL",
        "postgresql://ocr:ocr@127.0.0.1:5433/ocr_catalog",
    )


@contextmanager
def connect() -> Iterator[Any]:
    import psycopg

    with psycopg.connect(database_url()) as conn:
        conn.autocommit = False
        yield conn
        conn.commit()


def upsert_tag(conn: Any, name: str) -> int:
    row = conn.execute(
        """
        INSERT INTO tags (name) VALUES (%s)
        ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
        RETURNING id
        """,
        (name,),
    ).fetchone()
    return int(row[0])


def link_document_tags(conn: Any, document_id: int, tag_names: list[str]) -> None:
    conn.execute("DELETE FROM document_tags WHERE document_id = %s", (document_id,))
    for tag in tag_names:
        tag = tag.strip()
        if not tag:
            continue
        tag_id = upsert_tag(conn, tag)
        conn.execute(
            """
            INSERT INTO document_tags (document_id, tag_id)
            VALUES (%s, %s) ON CONFLICT DO NOTHING
            """,
            (document_id, tag_id),
        )


def upsert_category(conn: Any, name: str) -> int:
    row = conn.execute(
        """
        INSERT INTO categories (name) VALUES (%s)
        ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
        RETURNING id
        """,
        (name,),
    ).fetchone()
    return int(row[0])
