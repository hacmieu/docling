"""DeepSeek Q&A over staff search results (subset only, low cost)."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

import requests

from workspace.ocr_pipeline.concept_search import snippet_around
from workspace.ocr_pipeline.db_postgres import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = REPO_ROOT / ".env"
MAX_EXCERPT_CHARS = 3500
MAX_DOCS = 10

QA_PROMPT = """Bạn là trợ lý nội bộ Bệnh viện Hưng Thịnh.

Câu hỏi nhân viên: {question}

Dưới đây là tối đa {doc_count} đoạn trích từ tài liệu đã lọc (OCR). Chỉ trả lời dựa trên excerpt.
Nếu không đủ thông tin, nói rõ "không tìm thấy trong tập tài liệu đã lọc".

Trả lời tiếng Việt, ngắn gọn, có bullet nếu cần. Cuối câu trả lời liệt kê doc_id tham chiếu.

--- EXCERPTS ---
{excerpts}
"""


def text_api_config() -> dict[str, str]:
    load_dotenv(ENV_FILE)
    key = os.environ.get("AI_BOX_API_KEY", "").strip()
    url = os.environ.get("AI_BOX_API_URL", "https://api.ai-box.vn").rstrip("/")
    model = os.environ.get("AI_BOX_MODEL", "deepseek-v4-pro").strip()
    if not key:
        raise RuntimeError("AI_BOX_API_KEY missing in .env")
    return {"key": key, "url": url, "model": model}


def build_excerpts(
    items: list[dict[str, Any]],
    question: str,
) -> str:
    parts: list[str] = []
    budget = MAX_EXCERPT_CHARS
    for item in items[:MAX_DOCS]:
        doc_id = item.get("id")
        path = item.get("owncloud_path") or ""
        snippet = item.get("snippet") or item.get("summary") or ""
        if not snippet and item.get("markdown_head"):
            snippet = snippet_around(str(item["markdown_head"]), question)
        block = f"[doc_id={doc_id}] {path}\n{snippet}\n"
        if len(block) > budget:
            block = block[:budget] + "…\n"
        parts.append(block)
        budget -= len(block)
        if budget <= 0:
            break
    return "\n---\n".join(parts)


def call_deepseek_qa(question: str, excerpts: str, doc_count: int, cfg: dict[str, str]) -> str:
    prompt = QA_PROMPT.format(question=question, doc_count=doc_count, excerpts=excerpts)
    endpoint = f"{cfg['url']}/v1/chat/completions"
    payload = {
        "model": cfg["model"],
        "messages": [
            {
                "role": "system",
                "content": "Trả lời súc tích bằng tiếng Việt, chỉ dựa trên excerpt được cung cấp.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }
    headers = {"Authorization": f"Bearer {cfg['key']}", "Content-Type": "application/json"}
    for attempt in range(5):
        response = requests.post(endpoint, headers=headers, json=payload, timeout=120)
        if response.status_code == 429:
            time.sleep(min(60, 5 * (2**attempt)))
            continue
        response.raise_for_status()
        return str(response.json()["choices"][0]["message"]["content"]).strip()
    raise RuntimeError("AI API rate limited")


def answer_from_search_items(
    question: str,
    items: list[dict[str, Any]],
) -> dict[str, Any]:
    cfg = text_api_config()
    excerpts = build_excerpts(items, question)
    answer = call_deepseek_qa(question, excerpts, min(len(items), MAX_DOCS), cfg)
    ref_ids = [int(i["id"]) for i in items[:MAX_DOCS] if i.get("id") is not None]
    return {
        "question": question,
        "answer": answer,
        "reference_doc_ids": ref_ids,
        "model": cfg["model"],
        "excerpt_chars": len(excerpts),
        "estimated_tokens": max(1, len(excerpts) // 4),
    }


SYNTHESIZE_PROMPT = """Bạn là trợ lý nội bộ Bệnh viện Hưng Thịnh.

Câu hỏi: {question}

Dưới đây là metadata đã lọc từ catalog (doc_type, key_fields, summary). Chỉ trả lời dựa trên dữ liệu này.
Nếu không đủ thông tin, nói rõ phần nào thiếu. Trả lời tiếng Việt, có bullet nếu cần.
Cuối câu trả lời liệt kê doc_id tham chiếu.

--- DỮ LIỆU ĐÃ LỌC ---
{context}
"""


def synthesize_from_context_pack(
    question: str,
    context_block: str,
    *,
    doc_count: int = 0,
) -> dict[str, Any]:
    """DeepSeek synthesis over a pre-built llm_prompt_block."""
    cfg = text_api_config()
    prompt = SYNTHESIZE_PROMPT.format(question=question, context=context_block)
    endpoint = f"{cfg['url']}/v1/chat/completions"
    payload = {
        "model": cfg["model"],
        "messages": [
            {
                "role": "system",
                "content": "Trả lời súc tích bằng tiếng Việt, chỉ dựa trên context được cung cấp.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }
    headers = {"Authorization": f"Bearer {cfg['key']}", "Content-Type": "application/json"}
    for attempt in range(5):
        response = requests.post(endpoint, headers=headers, json=payload, timeout=120)
        if response.status_code == 429:
            time.sleep(min(60, 5 * (2**attempt)))
            continue
        response.raise_for_status()
        answer = str(response.json()["choices"][0]["message"]["content"]).strip()
        input_chars = len(prompt)
        return {
            "question": question,
            "answer": answer,
            "model": cfg["model"],
            "input_chars": input_chars,
            "estimated_tokens_input": max(1, input_chars // 4),
            "doc_count": doc_count,
        }
    raise RuntimeError("AI API rate limited")
