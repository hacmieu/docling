"""Pipeline lane configuration — all tunables via environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass

from workspace.ocr_pipeline.db_postgres import load_dotenv

REPO_ROOT = __import__("pathlib").Path(__file__).resolve().parents[2]
ENV_FILE = REPO_ROOT / ".env"


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


def _env_bool(key: str, *, default: bool) -> bool:
    raw = _env(key, "true" if default else "false").lower()
    return raw in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class PipelineConfig:
    """Two-lane extraction pipeline (configurable providers/models)."""

    # Lane 1: EasyOCR (or other) => RAW
    raw_ocr_engine: str
    raw_ocr_model: str
    source_raw: str

    # Lane 1 enrich: RAW text => AI metadata (deepseek-v4-pro or other)
    raw_enrich_model: str
    source_raw_enrich: str

    # Lane 2: AI Vision (Google or future providers) => OCR text
    vision_provider: str
    vision_model: str
    vision_api_url: str
    source_vision: str
    vision_priority: int

    # Lane 2 enrich: vision OCR text => AI metadata
    vision_enrich_provider: str
    vision_enrich_model: str
    vision_enrich_enabled: bool
    vision_enrich_fallback_inherit: bool

    # Shared text-enrich API (AI Box / OpenAI-compatible)
    enrich_api_url: str
    enrich_api_key: str
    enrich_max_chars: int

    vision_ocr_prompt: str
    vision_batch_sleep_seconds: float


def load_pipeline_config() -> PipelineConfig:
    load_dotenv(ENV_FILE)
    raw_enrich_model = _env("PIPELINE_RAW_ENRICH_MODEL") or _env("AI_BOX_MODEL", "deepseek-v4-pro")
    vision_enrich_model = (
        _env("PIPELINE_VISION_ENRICH_MODEL")
        or (_env("GOOGLE_VISION_MODEL", "gemini-2.5-flash") if _env("PIPELINE_VISION_PROVIDER", "google") == "google" else "")
        or raw_enrich_model
    )
    vision_enrich_provider = _env("PIPELINE_VISION_ENRICH_PROVIDER") or (
        "google" if _env("PIPELINE_VISION_PROVIDER", "google") == "google" else "aibox"
    )
    vision_model = _env("PIPELINE_VISION_MODEL") or _env("GOOGLE_VISION_MODEL", "gemini-2.5-flash")
    priority_raw = _env("PIPELINE_PRIORITY_VISION", "70")
    return PipelineConfig(
        raw_ocr_engine=_env("PIPELINE_RAW_OCR_ENGINE", "easyocr"),
        raw_ocr_model=_env("PIPELINE_RAW_OCR_MODEL", "docling-easyocr"),
        source_raw=_env("PIPELINE_SOURCE_RAW", "local_llm_ocr"),
        raw_enrich_model=raw_enrich_model,
        source_raw_enrich=_env("PIPELINE_SOURCE_RAW_ENRICH", "deepseek_cleanup"),
        vision_provider=_env("PIPELINE_VISION_PROVIDER", "google"),
        vision_model=vision_model,
        vision_api_url=_env("PIPELINE_VISION_API_URL")
        or _env("GOOGLE_API_URL", "https://generativelanguage.googleapis.com/v1beta"),
        source_vision=_env("PIPELINE_SOURCE_VISION", "google_vision"),
        vision_priority=int(priority_raw),
        vision_enrich_provider=vision_enrich_provider,
        vision_enrich_model=vision_enrich_model,
        vision_enrich_enabled=_env_bool("PIPELINE_VISION_ENRICH_ENABLED", default=True),
        vision_enrich_fallback_inherit=_env_bool(
            "PIPELINE_VISION_ENRICH_FALLBACK_INHERIT", default=False
        ),
        enrich_api_url=_env("PIPELINE_ENRICH_API_URL") or _env("AI_BOX_API_URL", "https://api.ai-box.vn"),
        enrich_api_key=_env("PIPELINE_ENRICH_API_KEY") or _env("AI_BOX_API_KEY", ""),
        enrich_max_chars=int(_env("PIPELINE_ENRICH_MAX_CHARS", "12000")),
        vision_ocr_prompt=_env(
            "PIPELINE_VISION_OCR_PROMPT",
            "OCR toàn bộ văn bản tiếng Việt trong ảnh. Trả về plain text, giữ xuống dòng hợp lý. "
            "Không thêm giải thích.",
        ),
        vision_batch_sleep_seconds=float(_env("PIPELINE_VISION_BATCH_SLEEP_SECONDS", "12")),
    )


def vision_api_key(config: PipelineConfig | None = None) -> str:
    cfg = config or load_pipeline_config()
    if cfg.vision_provider == "google":
        return _env("GOOGLE_API_KEY") or _env("GOOGLE_VISION_API_KEY")
    return _env(f"PIPELINE_VISION_API_KEY_{cfg.vision_provider.upper()}") or _env(
        "PIPELINE_VISION_API_KEY"
    )
