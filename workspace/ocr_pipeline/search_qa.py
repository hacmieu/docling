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


def estimate_tokens(text: str) -> int:
    """Rough token count (≈4 chars/token for Vietnamese + JSON)."""
    return max(1, len(text) // 4)


def build_synthesis_messages(
    question: str,
    context_block: str,
    doc_count: int,
) -> list[dict[str, str]]:
    """Build chat messages; context_block is metadata-only (no duplicate question header)."""
    user_content = (
        f"Bạn là trợ lý nội bộ Bệnh viện Hưng Thịnh.\n\n"
        f"NHIỆM VỤ: Trả lời CÂU HỎI bằng tiếng Việt, CHỈ dựa trên DỮ LIỆU CATALOG bên dưới "
        f"({doc_count} tài liệu). Không được yêu cầu người dùng đặt câu hỏi khác nếu đã có dữ liệu.\n"
        f"Cuối câu trả lời liệt kê doc_id tham chiếu.\n\n"
        f"CÂU HỎI:\n{question.strip()}\n\n"
        f"DỮ LIỆU CATALOG:\n{context_block.strip()}"
    )
    return [
        {
            "role": "system",
            "content": (
                "Tổng hợp metadata hành chính y tế. Luôn trả lời từ dữ liệu được cung cấp; "
                "không từ chối vì thiếu câu hỏi khi đã có block DỮ LIỆU CATALOG."
            ),
        },
        {"role": "user", "content": user_content},
    ]


def synthesize_from_context_pack(
    question: str,
    context_block: str,
    *,
    doc_count: int = 0,
) -> dict[str, Any]:
    """DeepSeek synthesis over a pre-built llm_prompt_block."""
    context_block = context_block.strip()
    if doc_count < 1:
        raise ValueError("doc_count phải >= 1 — bấm Tìm kiếm và chọn ít nhất 1 tài liệu")
    if len(context_block) < 80:
        raise ValueError("Context quá ngắn — dữ liệu catalog chưa được nạp vào prompt")

    cfg = text_api_config()
    messages = build_synthesis_messages(question, context_block, doc_count)
    user_content = messages[1]["content"]
    endpoint = f"{cfg['url']}/v1/chat/completions"
    payload = {
        "model": cfg["model"],
        "messages": messages,
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
        return {
            "question": question,
            "answer": answer,
            "model": cfg["model"],
            "input_chars": len(user_content),
            "estimated_tokens_input": estimate_tokens(user_content),
            "doc_count": doc_count,
            "context_chars": len(context_block),
        }
    raise RuntimeError("AI API rate limited")
