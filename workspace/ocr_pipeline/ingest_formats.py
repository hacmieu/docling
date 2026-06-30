"""Per-file-type ingest strategy — all lanes converge on documents.markdown."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from workspace.ocr_pipeline.db_postgres import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = REPO_ROOT / ".env"

# strategy tokens (configurable via PIPELINE_INGEST_<EXT>_STRATEGY)
STRATEGY_DOCLING_PARSE = "docling_parse"  # Office/HTML — structure → markdown, no bitmap OCR
STRATEGY_DOCLING_OCR = "docling_ocr"  # PDF / image — Docling + EasyOCR → markdown (lane 1 RAW)
STRATEGY_VISION_OCR = "vision_ocr"  # PDF page / image — AI vision → raw_text (lane 2)
STRATEGY_ASR = "asr"  # audio — Docling ASR extra
STRATEGY_SKIP = "skip"


@dataclass(frozen=True)
class IngestFormatSpec:
    extensions: frozenset[str]
    strategy: str
    description: str


def _env(key: str, default: str) -> str:
    return os.environ.get(key, default).strip()


def default_ingest_specs() -> tuple[IngestFormatSpec, ...]:
    """Default routing: Office=parse, PDF/images=OCR, audio=ASR."""
    return (
        IngestFormatSpec(
            frozenset({".pdf"}),
            _env("PIPELINE_INGEST_PDF_STRATEGY", STRATEGY_DOCLING_OCR),
            "PDF — Docling OCR → markdown; optional vision lane on rendered page",
        ),
        IngestFormatSpec(
            frozenset({".docx", ".doc"}),
            _env("PIPELINE_INGEST_DOCX_STRATEGY", STRATEGY_DOCLING_PARSE),
            "Word — Docling native parse → markdown (ưu tiên, không OCR ảnh)",
        ),
        IngestFormatSpec(
            frozenset({".xlsx", ".xls", ".ods"}),
            _env("PIPELINE_INGEST_XLSX_STRATEGY", STRATEGY_DOCLING_PARSE),
            "Excel — Docling table parse → markdown",
        ),
        IngestFormatSpec(
            frozenset({".pptx", ".ppt"}),
            _env("PIPELINE_INGEST_PPTX_STRATEGY", STRATEGY_DOCLING_PARSE),
            "PowerPoint — Docling parse → markdown",
        ),
        IngestFormatSpec(
            frozenset({".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"}),
            _env("PIPELINE_INGEST_IMAGE_STRATEGY", STRATEGY_DOCLING_OCR),
            "Ảnh — Docling image OCR → markdown; vision lane đọc file trực tiếp",
        ),
        IngestFormatSpec(
            frozenset({".m4a", ".mp3", ".wav"}),
            _env("PIPELINE_INGEST_AUDIO_STRATEGY", STRATEGY_ASR),
            "Audio — Docling ASR (cần extra asr) → text/markdown",
        ),
    )


def load_ingest_extensions() -> frozenset[str]:
    """Comma-separated allowlist, e.g. PIPELINE_INGEST_EXTENSIONS=.pdf,.docx,.jpg"""
    raw = _env(
        "PIPELINE_INGEST_EXTENSIONS",
        ".pdf,.docx,.xlsx,.pptx,.png,.jpg,.jpeg,.webp",
    )
    parts = {p.strip().lower() for p in raw.split(",") if p.strip()}
    return frozenset(p if p.startswith(".") else f".{p}" for p in parts)


def strategy_for_suffix(suffix: str) -> str | None:
    load_dotenv(ENV_FILE)
    ext = suffix.lower() if suffix.startswith(".") else f".{suffix.lower()}"
    if ext not in load_ingest_extensions():
        return None
    for spec in default_ingest_specs():
        if ext in spec.extensions:
            return spec.strategy
    return STRATEGY_DOCLING_OCR


def suffix_from_path(path: str) -> str:
    return Path(path).suffix.lower()


def is_ingest_allowed(path: str) -> bool:
    return suffix_from_path(path) in load_ingest_extensions()


def uses_docling_converter(strategy: str) -> bool:
    return strategy in {STRATEGY_DOCLING_PARSE, STRATEGY_DOCLING_OCR, STRATEGY_ASR}


def uses_vision_lane(strategy: str) -> bool:
    return strategy in {STRATEGY_DOCLING_OCR, STRATEGY_VISION_OCR}
