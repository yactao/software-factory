# app/routers/trading_doc.py
"""
POST /api/trading/doc — RAG over trading documents index (semantic search, Kimi synthesis).
Documents only (no images). Same response shape as /api/rag for frontend reuse.
"""

import re
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException

from ..core.security import _auth_dependency, _require_scope
from ..core.config import RETRIEVAL_K, TOPN_MAX
from ..models.schemas import TradingRequest
from ..services.history_helpers import _save_chat_event, _get_last_qna_pairs
from ..services.search_azure_trading_doc import search_trading_doc_chunks
from ..services.kimi_trading_doc_rag import synthesize_trading_doc_answer
from ..utils.query_refiner import _compose_search_query_from_history

router = APIRouter()

SMALLTALK_RE = re.compile(r"^\s*(bonjour|bonsoir|salut|slt|hello|hi)\b", re.I)

# Heuristic: French stopwords and accented chars vs English
_FR_STOPWORDS = {
    "le", "la", "les", "de", "des", "du", "un", "une", "au", "aux", "pour", "par",
    "sur", "dans", "avec", "que", "qui", "quoi", "dont", "où", "ce", "cet", "cette",
    "donne", "donnez", "moi", "mon", "ma", "mes", "est", "sont", "été", "être",
}
_EN_STOPWORDS = {"the", "and", "for", "with", "from", "this", "that", "what", "which", "have", "has", "are", "was"}


def detect_lang(question: str) -> str:
    """
    Detect language from question: 'fr' or 'en'.
    Heuristic: accents + common FR stopwords vs EN; fallback 'fr' when unsure.
    """
    q = (question or "").strip().lower()
    if not q:
        return "fr"

    # Accented chars often indicate French
    if re.search(r"[àâäéèêëïîôùûüçœæ]", q):
        return "fr"

    words = set(re.findall(r"[a-zàâäéèêëïîôùûüçœæ]+", q))
    fr_count = sum(1 for w in words if w in _FR_STOPWORDS)
    en_count = sum(1 for w in words if w in _EN_STOPWORDS)

    if en_count > fr_count:
        return "en"
    return "fr"


def _build_contexts_from_hits(
    hits: List[Dict[str, Any]],
    question: str,
    snippet_max: int = 1800,
) -> List[Dict[str, Any]]:
    """
    Build context list for synthesis. Each context:
      title: display_name or title
      snippet: caption_text + content trunc (cap snippet_max)
      meta: chunk_id, chunk_index, section, score, reranker
    """
    contexts: List[Dict[str, Any]] = []
    for d in hits:
        title = (d.get("display_name") or d.get("title") or "").strip() or "Document"
        caps = d.get("@search.captions") or []
        cap_text = (caps[0].get("text") if caps else "") or ""
        content = (d.get("content") or "").strip()
        combined = (cap_text + "\n" + content).strip() if cap_text else content
        snippet = combined[:snippet_max] if len(combined) > snippet_max else combined

        meta: Dict[str, Any] = {
            "chunk_id": d.get("chunk_id"),
            "chunk_index": d.get("chunk_index"),
            "section": d.get("section"),
            "score": d.get("@search.score"),
            "reranker": d.get("@search.rerankerScore"),
            "blob_name": d.get("blob_name"),
        }
        contexts.append({
            "title": title,
            "snippet": snippet,
            "meta": meta,
        })
    return contexts


def _make_used_doc_trading(context: Dict[str, Any]) -> Dict[str, Any]:
    """Build used_doc entry for frontend: title, path, snippet, score, meta."""
    meta = context.get("meta") or {}
    title = (context.get("title") or "Document").strip()
    path = meta.get("blob_name") or title  # no blob_uri; use blob_name or display title
    snippet = (context.get("snippet") or "")[:800]
    score = meta.get("score") or meta.get("reranker")
    return {
        "title": title,
        "path": path,
        "snippet": snippet,
        "score": score,
        "meta": {
            "chunk_index": meta.get("chunk_index"),
            "section": meta.get("section"),
            "score": meta.get("score"),
        },
    }


@router.post("/api/trading/doc")
def trading_doc(
    req: TradingRequest,
    claims: Dict[str, Any] = Depends(_auth_dependency),
):
    _require_scope(claims)

    question = (req.question or "").strip()
    if not question:
        raise HTTPException(400, "Question is empty.")

    conv_id = _save_chat_event(
        claims,
        req.conversation_id,
        role="user",
        route="trading_doc",
        message=question,
        meta={"filters": req.filters, "top_k": req.top_k},
    )

    # Smalltalk: short answer and return
    if SMALLTALK_RE.search(question):
        payload = {
            "answer": "Bonjour. Posez une question sur vos documents de trading pour que je puisse répondre.",
            "citations": [],
            "used_docs": [],
            "conversation_id": conv_id,
            "model": "Aïna Instant",
        }
        _save_chat_event(
            claims,
            conv_id,
            role="assistant",
            route="trading_doc",
            message=payload["answer"],
            meta=payload,
        )
        return payload

    lang = detect_lang(question)

    # History for query refinement and synthesis
    try:
        history_pairs = _get_last_qna_pairs(
            claims, conv_id, route="trading_doc", max_pairs=3
        )
        if history_pairs and (history_pairs[-1].get("user") or "").strip() == question:
            history_pairs = history_pairs[:-1]
    except Exception:
        history_pairs = []

    effective_question, refine_meta = _compose_search_query_from_history(
        question, history_pairs
    )
    try:
        _save_chat_event(
            claims,
            conv_id,
            role="meta",
            route="meta",
            message="",
            meta={
                "type": "query_refined",
                "original": question,
                "refined": effective_question,
                "language": lang,
                **refine_meta,
            },
        )
    except Exception:
        pass

    k = max(1, min(req.top_k or RETRIEVAL_K, TOPN_MAX))
    try:
        search_result = search_trading_doc_chunks(
            effective_question,
            req.filters,
            k=k,
            language=lang,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, f"Search error: {e}")

    hits = search_result.get("value", []) or []
    if not hits:
        payload = {
            "answer": "Je ne trouve pas d'information pertinente dans les documents de trading pour cette question.",
            "citations": [],
            "used_docs": [],
            "conversation_id": conv_id,
            "model": "Aïna Instant",
        }
        _save_chat_event(
            claims,
            conv_id,
            role="assistant",
            route="trading_doc",
            message=payload["answer"],
            meta={**payload, "language": lang, "refined_query": effective_question},
        )
        return payload

    contexts = _build_contexts_from_hits(hits, effective_question, snippet_max=1800)

    try:
        answer_text, uses_context, used_indices = synthesize_trading_doc_answer(
            question=question,
            contexts=contexts,
            chat_history_pairs=history_pairs,
        )
    except Exception as e:
        raise HTTPException(503, f"Synthesis error: {e}")

    if used_indices:
        used_docs = [
            _make_used_doc_trading(contexts[i - 1])
            for i in used_indices
            if 1 <= i <= len(contexts)
        ]
    elif uses_context:
        used_docs = [
            _make_used_doc_trading(c)
            for c in contexts[: min(3, len(contexts))]
        ]
    else:
        used_docs = []

    resp_payload = {
        "answer": answer_text,
        "citations": [],
        "used_docs": used_docs,
        "conversation_id": conv_id,
        "model": "Aïna Instant",
    }

    _save_chat_event(
        claims,
        conv_id,
        role="assistant",
        route="trading_doc",
        message=resp_payload["answer"],
        meta={
            **resp_payload,
            "refined_query": effective_question,
            "language": lang,
            "filters": req.filters,
            **refine_meta,
        },
    )
    return resp_payload
