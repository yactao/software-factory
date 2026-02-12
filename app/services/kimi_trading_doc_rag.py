# app/services/kimi_trading_doc_rag.py
"""
Synthesis of RAG answers for trading documents using Kimi (Moonshot) via llm_provider.
Output: JSON with answer, uses_context, used_sources (1-based indices).
"""

import json
from typing import List, Dict, Any, Tuple

from app.services.llm_provider import llm_chat_completion

SNIPPET_MAX = 1800


def synthesize_trading_doc_answer(
    question: str,
    contexts: List[Dict[str, Any]],
    chat_history_pairs: List[Dict[str, str]],
) -> Tuple[str, bool, List[int]]:
    """
    Synthesize an answer from trading-doc contexts using the RAG LLM (Kimi).

    Returns:
        (answer_text, uses_context, used_source_indices)
        where used_source_indices are 1-based indices into contexts.
    """
    if not contexts:
        return (
            "I could not find enough information in the provided documents to answer precisely.",
            False,
            [],
        )

    sources_block_lines = []
    for idx, c in enumerate(contexts, start=1):
        title = c.get("title") or f"Source {idx}"
        snippet = (c.get("snippet") or "").strip()
        if len(snippet) > SNIPPET_MAX:
            snippet = snippet[:SNIPPET_MAX] + "..."
        sources_block_lines.append(f"[{idx}] {title}\n{snippet}")
    sources_block = "\n\n".join(sources_block_lines)

    hist_lines = []
    for pair in chat_history_pairs[-3:]:
        u = (pair.get("user") or "").strip()
        a = (pair.get("assistant") or "").strip()
        if u:
            hist_lines.append(f"U: {u}")
        if a:
            hist_lines.append(f"A: {a}")
    history_text = "\n".join(hist_lines)

    system_prompt = (
        "You are an enterprise assistant for a RAG system over a trading documents knowledge base.\n"
        "You must answer ONLY from the SOURCES provided. If information is not in the sources, say so and do not invent anything.\n\n"
        "Language: answer in the same language as the user question (French or English).\n\n"
        "Output format: STRICTLY valid UTF-8 JSON, no text before or after. Booleans must be true or false without quotes.\n"
        "Expected structure:\n"
        "{\n"
        '  "answer": "your answer text",\n'
        '  "uses_context": true,\n'
        '  "used_sources": [1, 2, 3]\n'
        "}\n"
    )

    user_prompt = (
        "USER QUESTION:\n"
        f"{question}\n\n"
        "RECENT CONVERSATION (optional):\n"
        f"{history_text}\n\n"
        "AVAILABLE SOURCES:\n"
        f"{sources_block}\n\n"
        "Reply with JSON conforming to the required schema."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    try:
        raw = llm_chat_completion(
            "rag_single",
            messages,
            temperature=0.1,
            max_tokens=1100,
        )
        raw_str = (raw or "").strip()

        try:
            obj = json.loads(raw_str)
        except Exception:
            start = raw_str.find("{")
            end = raw_str.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    obj = json.loads(raw_str[start : end + 1])
                except Exception:
                    return raw_str, True, []
            else:
                return raw_str, True, []

    except Exception as e:
        return (
            f"Synthesis unavailable. Details: {e}",
            False,
            [],
        )

    answer = (obj.get("answer") or "").strip()
    uses_context = bool(obj.get("uses_context", True))
    used_sources = obj.get("used_sources") or []

    used_indices: List[int] = []
    for i in used_sources:
        try:
            i_int = int(i)
        except Exception:
            continue
        if 1 <= i_int <= len(contexts):
            used_indices.append(i_int)

    if not answer:
        answer = "Empty response."

    return answer, uses_context, used_indices
