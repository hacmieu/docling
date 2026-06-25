# Report Entry - OwnCloud Version Correction

## Clarification delivered

| Product | Relationship | Used now? |
|---------|--------------|-----------|
| Nextcloud | Fork of ownCloud (2016) | No |
| ownCloud Server 10.x | Legacy PHP ownCloud | Replaced |
| ownCloud Infinite Scale 8.0.4 | Current ownCloud product | Yes |

## Code changes

- `infra/docker-compose.yml`: `owncloud/ocis:8.0.4` replaces `owncloud/server` + MariaDB.
- `owncloud_sync_catalog.py`: HTTPS + `OWNCLOUD_INSECURE` for OCIS self-signed cert.
- `infra/README.md`: product comparison table added.
