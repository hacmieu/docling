#!/usr/bin/env python3
"""Download cataloged files from OCIS, OCR with Docling, update PostgreSQL with SLA timing."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

import requests
import xml.etree.ElementTree as ET

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.folder_to_sqlite_mvp import build_converter, sha256sum
from scripts.owncloud_sync_catalog import (
    normalize_path,
    owncloud_config,
    resolve_drive,
)
from workspace.ocr_pipeline.db_postgres import connect, load_dotenv

PDF_SUFFIXES = {".pdf"}


@dataclass
class SlaRecord:
    document_id: int
    owncloud_path: str
    status: str
    started_at: str
    finished_at: str
    duration_seconds: float
    markdown_len: int
    error_message: str | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=10, help="Max files to OCR.")
    parser.add_argument(
        "--drive-alias",
        default="project/hth-shared-drive",
        help="OCIS drive alias filter.",
    )
    parser.add_argument(
        "--only-pdf",
        action="store_true",
        default=True,
        help="Only process PDF files (default: true).",
    )
    parser.add_argument("--ocr-engine", choices=["easyocr", "tesseract", "ocrmac"], default="easyocr")
    parser.add_argument("--ocr-lang", default="vi,en")
    parser.add_argument("--easyocr-confidence-threshold", type=float, default=0.25)
    parser.add_argument("--force-full-page-ocr", action="store_true", default=True)
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=REPO_ROOT / "workspace/ocr_pipeline/03_processing/ocr_downloads",
    )
    parser.add_argument(
        "--sla-report",
        type=Path,
        default=None,
        help="JSON SLA report path (default: 09_logs/YYYYMMDD_HHMM-ocr-sla.json).",
    )
    return parser.parse_args()


def ocr_args_namespace(args: argparse.Namespace) -> argparse.Namespace:
    return argparse.Namespace(
        enable_ocr=True,
        force_full_page_ocr=args.force_full_page_ocr,
        ocr_engine=args.ocr_engine,
        ocr_lang=args.ocr_lang,
        easyocr_confidence_threshold=args.easyocr_confidence_threshold,
        ocr_psm=None,
        ocrmac_recognition="accurate",
    )


def catalog_rel_path(owncloud_path: str, drive_alias: str) -> str:
    path = normalize_path(owncloud_path)
    prefix = f"{drive_alias}/"
    if path.startswith(prefix):
        return path[len(prefix) :]
    if path.startswith("/"):
        return path.lstrip("/")
    return path


def find_dav_href(cfg: dict[str, str], drive: dict[str, str], rel_path: str) -> str:
    """Resolve WebDAV href by walking folders (matches OCIS encoding)."""
    DAV = "{DAV:}"
    current_href = drive["dav_href_prefix"]
    if not current_href.endswith("/"):
        current_href += "/"
    parts = [p for p in normalize_path(rel_path).split("/") if p]

    for index, part in enumerate(parts):
        request_url = f"{cfg['base']}{current_href}" if current_href.startswith("/") else current_href
        response = requests.request(
            "PROPFIND",
            request_url,
            auth=(cfg["user"], cfg["password"]),
            headers={"Depth": "1"},
            timeout=120,
            verify=not cfg["insecure"],
        )
        response.raise_for_status()
        target_norm = normalize_path(part)
        matched_href: str | None = None
        for response_el in ET.fromstring(response.content).findall(f"{DAV}response"):
            href_el = response_el.find(f"{DAV}href")
            if href_el is None or href_el.text is None:
                continue
            href = href_el.text
            name = normalize_path(href.rstrip("/").rsplit("/", 1)[-1])
            if name == target_norm:
                matched_href = href
                break
        if matched_href is None:
            raise FileNotFoundError(f"OCIS path segment not found: {part} under {current_href}")
        if index == len(parts) - 1:
            return matched_href
        current_href = matched_href if matched_href.endswith("/") else matched_href + "/"
    raise FileNotFoundError(f"Could not resolve href for: {rel_path}")


def download_file(cfg: dict[str, str], drive: dict[str, str], rel_path: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    href = find_dav_href(cfg, drive, rel_path)
    url = f"{cfg['base']}{href}" if href.startswith("/") else href
    response = requests.get(
        url,
        auth=(cfg["user"], cfg["password"]),
        timeout=300,
        verify=not cfg["insecure"],
        stream=True,
    )
    response.raise_for_status()
    with dest.open("wb") as handle:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                handle.write(chunk)


def select_documents(
    drive_alias: str,
    limit: int,
    only_pdf: bool,
) -> list[tuple[int, str]]:
    pattern = f"{drive_alias}%"
    suffix_clause = "AND lower(owncloud_path) LIKE '%%.pdf'" if only_pdf else ""
    with connect() as conn:
        rows = conn.execute(
            f"""
            SELECT id, owncloud_path
            FROM documents
            WHERE owncloud_path LIKE %s
              AND status = 'cataloged'
              AND coalesce(markdown, '') = ''
              AND owncloud_path NOT ILIKE '%%.DS_Store'
              {suffix_clause}
            ORDER BY id
            LIMIT %s
            """,
            (pattern, limit),
        ).fetchall()
    return [(int(row[0]), normalize_path(row[1])) for row in rows]


def update_success(
    conn,
    doc_id: int,
    file_hash: str,
    local_path: str,
    markdown: str,
    doc_dict: dict,
    sla: SlaRecord,
    now: datetime,
) -> None:
    doc_dict = dict(doc_dict)
    doc_dict["ocr_sla"] = {
        "started_at": sla.started_at,
        "finished_at": sla.finished_at,
        "duration_seconds": sla.duration_seconds,
        "engine": "docling",
    }
    conn.execute(
        """
        UPDATE documents SET
            local_path = %s,
            source_path = %s,
            source_sha256 = %s,
            markdown = %s,
            doc_json = %s::jsonb,
            status = 'success',
            error_message = NULL,
            updated_at = %s
        WHERE id = %s
        """,
        (
            local_path,
            local_path,
            file_hash,
            markdown,
            json.dumps(doc_dict, ensure_ascii=False),
            now,
            doc_id,
        ),
    )


def update_failure(
    conn,
    doc_id: int,
    error_message: str,
    sla: SlaRecord,
    now: datetime,
) -> None:
    conn.execute(
        """
        UPDATE documents SET
            status = 'failure',
            error_message = %s,
            doc_json = coalesce(doc_json, '{}'::jsonb) || %s::jsonb,
            updated_at = %s
        WHERE id = %s
        """,
        (
            error_message,
            json.dumps({"ocr_sla": asdict(sla)}, ensure_ascii=False),
            now,
            doc_id,
        ),
    )


def default_sla_report_path() -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    return REPO_ROOT / f"workspace/ocr_pipeline/09_logs/{stamp}-ocr-sla.json"


def main() -> int:
    load_dotenv()
    args = parse_args()
    cfg = owncloud_config()
    drive = resolve_drive(cfg, args.drive_alias)
    candidates = select_documents(args.drive_alias, args.limit, args.only_pdf)
    if not candidates:
        print("No cataloged documents pending OCR.")
        return 0

    converter = build_converter(ocr_args_namespace(args))
    batch_started = datetime.now(UTC)
    batch_t0 = time.perf_counter()
    sla_records: list[SlaRecord] = []

    print(f"Batch OCR start: {batch_started.isoformat()} files={len(candidates)}")

    for doc_id, owncloud_path in candidates:
        rel = catalog_rel_path(owncloud_path, args.drive_alias)
        local_file = args.work_dir / rel
        started_at = datetime.now(UTC)
        t0 = time.perf_counter()
        sla = SlaRecord(
            document_id=doc_id,
            owncloud_path=owncloud_path,
            status="pending",
            started_at=started_at.isoformat(),
            finished_at="",
            duration_seconds=0.0,
            markdown_len=0,
        )
        try:
            print(f"[START] id={doc_id} {owncloud_path}")
            download_file(cfg, drive, rel, local_file)
            file_hash = sha256sum(local_file)
            result = converter.convert(local_file)
            markdown = result.document.export_to_markdown()
            doc_dict = result.document.export_to_dict()
            finished_at = datetime.now(UTC)
            duration = time.perf_counter() - t0
            sla.status = "success"
            sla.finished_at = finished_at.isoformat()
            sla.duration_seconds = round(duration, 3)
            sla.markdown_len = len(markdown)
            with connect() as conn:
                update_success(
                    conn,
                    doc_id,
                    file_hash,
                    str(local_file.resolve()),
                    markdown,
                    doc_dict,
                    sla,
                    finished_at,
                )
            print(
                f"[OK] id={doc_id} duration={sla.duration_seconds}s md_len={sla.markdown_len}"
            )
        except Exception as exc:
            finished_at = datetime.now(UTC)
            duration = time.perf_counter() - t0
            sla.status = "failure"
            sla.finished_at = finished_at.isoformat()
            sla.duration_seconds = round(duration, 3)
            sla.error_message = str(exc)
            with connect() as conn:
                update_failure(conn, doc_id, str(exc), sla, finished_at)
            print(f"[FAIL] id={doc_id} duration={sla.duration_seconds}s error={exc}")

        sla_records.append(sla)

    batch_finished = datetime.now(UTC)
    batch_duration = round(time.perf_counter() - batch_t0, 3)
    success = sum(1 for r in sla_records if r.status == "success")
    failure = len(sla_records) - success

    report = {
        "batch_started_at": batch_started.isoformat(),
        "batch_finished_at": batch_finished.isoformat(),
        "batch_duration_seconds": batch_duration,
        "files_total": len(sla_records),
        "files_success": success,
        "files_failure": failure,
        "avg_duration_seconds": round(
            sum(r.duration_seconds for r in sla_records) / max(len(sla_records), 1), 3
        ),
        "ocr_engine": args.ocr_engine,
        "drive_alias": args.drive_alias,
        "records": [asdict(r) for r in sla_records],
    }

    report_path = args.sla_report or default_sla_report_path()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        f"Batch OCR end: {batch_finished.isoformat()} "
        f"duration={batch_duration}s success={success} failure={failure}"
    )
    print(f"SLA report: {report_path}")
    return 0 if failure == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
