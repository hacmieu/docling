"""Source types and priority scores for document extraction versions."""

from __future__ import annotations

SOURCE_PRIORITY: dict[str, int] = {
    "human_verified": 100,
    "human_webchat": 95,
    "google_vision": 70,
    "deepseek_cleanup": 50,
    "local_llm_ocr": 30,
}

SOURCE_LABELS_VI: dict[str, str] = {
    "human_verified": "Người xác nhận",
    "human_webchat": "Người (Webchat AI)",
    "google_vision": "Google Vision",
    "deepseek_cleanup": "DeepSeek làm sạch OCR",
    "local_llm_ocr": "OCR local (EasyOCR)",
}


def priority_for(source_type: str) -> int:
    return SOURCE_PRIORITY.get(source_type, 0)


def winning_source(sources: list[tuple[str, int]]) -> str | None:
    """Pick source_type with highest priority; ties broken by order."""
    if not sources:
        return None
    return max(sources, key=lambda item: item[1])[0]
