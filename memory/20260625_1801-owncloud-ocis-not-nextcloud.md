# Memory Entry - OwnCloud Product Line Clarification

- Previous stack used `owncloud/server:10.15` (ownCloud Server legacy, **not** Nextcloud).
- User requirement: latest **ownCloud GmbH** product, not Nextcloud fork.
- Updated infra to **ownCloud Infinite Scale (OCIS) `owncloud/ocis:8.0.4`** (production line, May 2026).
- UI: https://127.0.0.1:9200 | WebDAV sync script updated for OCIS + insecure TLS.
