#!/usr/bin/env python3
"""Sync OwnCloud/WebDAV paths into PostgreSQL catalog (metadata only)."""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from urllib.parse import quote, unquote, urljoin

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workspace.ocr_pipeline.db_postgres import connect, load_dotenv

DAV_NS = {"d": "DAV:"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--remote-prefix",
        default="/",
        help="Folder under the drive root (default: /).",
    )
    parser.add_argument(
        "--drive-alias",
        default=None,
        help="OCIS drive alias, e.g. project/hth-shared-drive (uses personal space if omitted).",
    )
    parser.add_argument(
        "--local-sync-dir",
        type=Path,
        default=None,
        help="Optional local OwnCloud sync folder; used to compute sha256 when file exists.",
    )
    return parser.parse_args()


def owncloud_config() -> dict[str, str]:
    load_dotenv()
    base = os.environ.get("OWNCLOUD_URL", "https://127.0.0.1:9200").rstrip("/")
    user = os.environ.get("OWNCLOUD_USER", "admin")
    password = os.environ.get("OWNCLOUD_PASSWORD", "admin")
    insecure = os.environ.get("OWNCLOUD_INSECURE", "true").lower() in (
        "1",
        "true",
        "yes",
    )
    return {"base": base, "user": user, "password": password, "insecure": insecure}


def dav_root(cfg: dict[str, str]) -> str:
    return f"{cfg['base']}/remote.php/dav/files/{quote(cfg['user'])}/"


def resolve_drive(cfg: dict[str, str], drive_alias: str | None) -> dict[str, str]:
    if drive_alias is None:
        personal_href = f"/remote.php/dav/files/{cfg['user']}/"
        return {
            "alias": f"personal/{cfg['user']}",
            "dav_href_prefix": personal_href,
            "href_marker": f"/files/{cfg['user']}/",
        }

    response = requests.get(
        f"{cfg['base']}/graph/v1beta1/me/drives",
        auth=(cfg["user"], cfg["password"]),
        timeout=60,
        verify=not cfg["insecure"],
    )
    response.raise_for_status()
    for drive in response.json().get("value", []):
        if drive.get("driveAlias") == drive_alias:
            web_dav_url = drive.get("root", {}).get("webDavUrl", "")
            if not web_dav_url:
                break
            dav_path = web_dav_url.removeprefix(cfg["base"])
            if not dav_path.endswith("/"):
                dav_path += "/"
            return {
                "alias": drive_alias,
                "dav_href_prefix": dav_path,
                "href_marker": dav_path,
            }
    raise SystemExit(f"Drive alias not found: {drive_alias}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def list_remote_files(
    cfg: dict[str, str],
    drive: dict[str, str],
    prefix: str,
) -> list[str]:
    """List files under prefix via WebDAV PROPFIND (OCIS rejects Depth: infinity)."""
    start_href = urljoin(drive["dav_href_prefix"], prefix.lstrip("/"))
    if not start_href.endswith("/"):
        start_href += "/"

    dirs_to_scan: list[str] = [start_href]
    file_paths: list[str] = []
    seen_dirs: set[str] = set()
    skip_names = {".space"}

    while dirs_to_scan:
        target_href = dirs_to_scan.pop()
        if target_href in seen_dirs:
            continue
        seen_dirs.add(target_href)

        request_url = f"{cfg['base']}{target_href}"

        response = requests.request(
            "PROPFIND",
            request_url,
            auth=(cfg["user"], cfg["password"]),
            headers={"Depth": "1"},
            timeout=120,
            verify=not cfg["insecure"],
        )
        response.raise_for_status()

        for response_el in ET.fromstring(response.content).findall("d:response", DAV_NS):
            href_el = response_el.find("d:href", DAV_NS)
            if href_el is None or href_el.text is None:
                continue
            href = href_el.text
            if href.endswith("/"):
                name = href.rstrip("/").rsplit("/", 1)[-1]
                if name in skip_names:
                    continue
                if href != target_href and href not in seen_dirs:
                    dirs_to_scan.append(href)
                continue
            rel = unquote(href.split(drive["href_marker"], 1)[-1].lstrip("/"))
            if not rel or rel.split("/", 1)[0] in skip_names:
                continue
            if drive["alias"].startswith("personal/"):
                file_paths.append("/" + rel)
            else:
                file_paths.append(f"{drive['alias']}/{rel}")

    return sorted(set(file_paths))


def upsert_catalog_row(
    conn,
    owncloud_path: str,
    local_path: str | None,
    file_hash: str,
    now_iso: datetime,
) -> None:
    conn.execute(
        """
        INSERT INTO documents (
            owncloud_path, local_path, source_path, source_sha256,
            markdown, doc_json, status, created_at, updated_at
        )
        VALUES (%s, %s, %s, %s, '', '{}'::jsonb, 'cataloged', %s, %s)
        ON CONFLICT (owncloud_path) DO UPDATE SET
            local_path = EXCLUDED.local_path,
            source_path = COALESCE(documents.source_path, EXCLUDED.source_path),
            source_sha256 = EXCLUDED.source_sha256,
            updated_at = EXCLUDED.updated_at
        """,
        (
            owncloud_path,
            local_path,
            local_path or owncloud_path,
            file_hash,
            now_iso,
            now_iso,
        ),
    )


def main() -> int:
    args = parse_args()
    cfg = owncloud_config()
    drive = resolve_drive(cfg, args.drive_alias)
    now = datetime.now(UTC)
    remote_files = list_remote_files(cfg, drive, args.remote_prefix)
    if not remote_files:
        print("No remote files found.")
        return 0

    synced = 0
    with connect() as conn:
        for owncloud_path in remote_files:
            local_path: str | None = None
            file_hash = "0" * 64
            if args.local_sync_dir:
                local_candidate = args.local_sync_dir / owncloud_path.lstrip("/")
                if local_candidate.is_file():
                    local_path = str(local_candidate.resolve())
                    file_hash = sha256_file(local_candidate)
            upsert_catalog_row(conn, owncloud_path, local_path, file_hash, now)
            synced += 1
            print(f"[SYNC] {owncloud_path}")

    print(f"Completed OwnCloud catalog sync. files={synced}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
