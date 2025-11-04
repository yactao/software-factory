from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from ..core.security import _auth_dependency, _require_scope
from ..core.config import RETRIEVAL_K, TOPN_MAX
from ..models.schemas import RAGRequest
from ..services.history_helpers import _save_chat_event
from ..services.search_azure import _search_docs
from ..services.gemini_rag import _synthesize_with_citations
from ..utils.snippets import _extract_path, _extract_title, _is_in_scope, _make_used_doc_from_context, _prefer_answer_or_focused_snippet
from ..utils.query_refiner import _compose_search_query_from_history
from ..services.history_helpers import _get_last_qna_pairs

import re

router = APIRouter()
SMALLTALK_RE = re.compile(r"^\s*(bonjour|bonsoir|salut|slt|hello|hi)\b", re.I)

@router.post("/api/rag")
def rag(req: RAGRequest, claims: Dict[str, Any] = Depends(_auth_dependency)):
    _require_scope(claims)

    question = (req.question or "").strip()
    if not question:
        raise HTTPException(400, "Question is empty.")

    conv_id = _save_chat_event(
        claims,
        req.conversation_id,
        role="user",
        route="rag",
        message=question,
        meta={"filters": req.filters, "top_k": req.top_k}
    )

    if SMALLTALK_RE.search(question):
        payload = {
            "answer": "Bonjour. Posez une question liée à vos documents pour que je puisse répondre.",
            "citations": [],
            "used_docs": [],
            "conversation_id": conv_id,
        }
        _save_chat_event(claims, conv_id, role="assistant", route="rag",
                         message=payload["answer"], meta=payload)
        return payload

    # 1) Récupère 3 derniers couples exacts U/A
    try:
        history_pairs = _get_last_qna_pairs(claims, conv_id, route="rag", max_pairs=3)
        if history_pairs and history_pairs[-1].get("user","").strip() == question:
            history_pairs = history_pairs[:-1]
    except Exception:
        history_pairs = []

    # 2) Mini-agent: compose une requête complète à partir de l’historique (sinon as_is)
    effective_question, refine_meta = _compose_search_query_from_history(question, history_pairs)

    # 3) Log meta de raffinement (utile pour debug)
    try:
        _save_chat_event(
            claims,
            conversation_id=conv_id,
            role="meta",
            route="meta",
            message="",
            meta={"type": "query_refined", "original": question, "refined": effective_question, **refine_meta}
        )
    except Exception:
        pass

    # 4) Recherche Azure Search avec la question raffinée
    search_json = _search_docs(effective_question, req.filters, k=RETRIEVAL_K)
    hits = search_json.get("value", []) or []
    answers = search_json.get("@search.answers", []) or []

    if not _is_in_scope(hits) and not answers:
        payload = {
            "answer": "Je ne trouve pas d’information pertinente dans les documents fournis pour cette question.",
            "citations": [],
            "used_docs": [],
            "conversation_id": conv_id,
        }
        _save_chat_event(claims, conv_id, role="assistant", route="rag",
                         message=payload["answer"], meta=payload)
        return payload

    # 5) Contexte LLM (answers + documents). Pour les fenêtres sans caption,
    #    on centre le snippet sur 'effective_question' (pas la question brute).
    N = max(1, min(req.top_k or TOPN_MAX, TOPN_MAX))
    contexts: List[Dict[str, Any]] = []

    if answers:
        try:
            answers_sorted = sorted(answers, key=lambda a: a.get("score", 0), reverse=True)
        except Exception:
            answers_sorted = answers
        best_ans = answers_sorted[0]
        ans_text = (best_ans.get("text") or "").strip()
        if ans_text:
            contexts.append({
                "title": "Azure AI Search — Réponse",
                "snippet": ans_text,
                "meta": {"kind": "answer", "key": best_ans.get("key"), "score": best_ans.get("score")},
            })

    for d in hits[:N]:
        doc_title = _extract_title(d)
        doc_path  = _extract_path(d)
        caps = d.get("@search.captions") or []
        cap_text = caps[0].get("text") if caps else ""
        snippet = (
            (cap_text + "\n" + (d.get("content") or ""))[:1800]
            if cap_text else _prefer_answer_or_focused_snippet(effective_question, d)
        )
        contexts.append({
            "title": doc_title,
            "snippet": snippet,
            "meta": {"id": d.get("id"), "path": doc_path, "score": d.get("@search.score"), "reranker": d.get("@search.rerankerScore")},
        })

    if not contexts:
        payload = {
            "answer": "Je ne trouve pas d’information pertinente dans les documents fournis pour cette question.",
            "citations": [],
            "used_docs": [],
            "conversation_id": conv_id,
        }
        _save_chat_event(claims, conv_id, role="assistant", route="rag",
                         message=payload["answer"], meta=payload)
        return payload

    # 6) Synthèse finale avec historique (toujours séparé des SOURCES)
    answer, uses_context, used_list = _synthesize_with_citations(
        question=question,                    # on répond à la question utilisateur
        contexts=contexts,                    # mais les passages viennent de la recherche sur effective_question
        chat_history_pairs=history_pairs
    )

    def _is_doc_context(c: Dict[str, Any]) -> bool:
        return c.get("meta", {}).get("kind") != "answer"

    if used_list:
        selected = []
        for i in used_list:
            if 1 <= i <= len(contexts):
                c = contexts[i - 1]
                if _is_doc_context(c):
                    selected.append(c)
        used_docs = [_make_used_doc_from_context(c) for c in selected]
    elif uses_context:
        doc_contexts = [c for c in contexts if _is_doc_context(c)]
        selected = doc_contexts[: min(3, len(doc_contexts))]
        used_docs = [_make_used_doc_from_context(c) for c in selected]
    else:
        used_docs = []

    resp_payload = {
        "answer": answer,
        "citations": [],
        "used_docs": used_docs,
        "conversation_id": conv_id,
    }
    _save_chat_event(claims, conv_id, role="assistant", route="rag", message=answer,
                     meta={**resp_payload, "refined_query": effective_question, **refine_meta})
    return resp_payload
