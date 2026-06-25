# Report Entry - Vietnamese OCR Enhancement

## Implemented changes

- Updated `scripts/folder_to_sqlite_mvp.py` to expose OCR tuning parameters.
- Script now supports selecting OCR engine and passing language-specific options.
- Defaults now target Vietnamese-first extraction when OCR is enabled.

## Verified

- CLI check passed: `python scripts/folder_to_sqlite_mvp.py --help`.
- Lint diagnostics for touched file: no issues.
