from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
import re

from app.core.security import _auth_dependency, _require_scope
from app.core.config import VET_RETRIEVAL_K, TOPN_MAX
from app.models.schemas import RAGRequest

from app.services.history_helpers import _save_chat_event, _get_last_qna_pairs
from app.services.search_vet_azure import _search_vet_docs
from app.services.vet_kimi import _synthesize_vet_with_citations
from app.utils.query_refiner import _compose_search_query_from_history
from app.utils.snippets import (
    _is_in_scope,
    _make_used_doc_from_context,
    _prefer_answer_or_focused_snippet,
)

router = APIRouter()
SMALLTALK_RE = re.compile(r"^\s*(bonjour|bonsoir|salut|slt|hello|hi)\b", re.I)


def _extract_title_vet(d: Dict[str, Any]) -> str:
    """
    Titre simple pour les docs vet : on privilégie file_name.
    """
    return (d.get("file_name") or d.get("category") or "Document vétérinaire").strip()


def _extract_path_vet(d: Dict[str, Any]) -> str | None:
    """
    Pour l'index vet, on stocke normalement blob_path (url du blob).
    """
    return d.get("blob_path") or None


@router.post("/api/vet-doc")
def vet_doc_rag(req: RAGRequest, claims: Dict[str, Any] = Depends(_auth_dependency)):
    """
    RAG dédié aux documents vétérinaires (vet-knowledge-index) avec synthèse Kimi spécifique.
    - Index: vet-knowledge-index
    - Pas de logique magasin / images
    - Réponses structurées à partir des procédures / diagnostics / RH / RGPD
    """
    _require_scope(claims)

    question = (req.question or "").strip()
    if not question:
        raise HTTPException(400, "Question is empty.")

    # 0) Sauvegarde message user (route = 'vet_doc' pour distinguer)
    conv_id = _save_chat_event(
        claims,
        req.conversation_id,
        role="user",
        route="vet_doc",
        message=question,
        meta={"filters": req.filters, "top_k": req.top_k},
    )

    # Small talk → réponse courte générique
    if SMALLTALK_RE.search(question):
        payload = {
            "answer": "Bonjour. Posez une question liée aux procédures médicales, diagnostics ou aux règles RH / RGPD du centre vétérinaire.",
            "citations": [],
            "used_docs": [],
            "conversation_id": conv_id,
            "images": [],
            "model": "Aïna Vet",
        }
        _save_chat_event(
            claims,
            conv_id,
            role="assistant",
            route="vet_doc",
            message=payload["answer"],
            meta=payload,
        )
        return payload

    # 1) Historique Q/A récent pour raffiner la requête
    try:
        history_pairs = _get_last_qna_pairs(claims, conv_id, route="vet_doc", max_pairs=3)
        if history_pairs and history_pairs[-1].get("user", "").strip() == question:
            history_pairs = history_pairs[:-1]
    except Exception:
        history_pairs = []

    # 2) Raffinement de la requête (Gemini)
    effective_question, refine_meta = _compose_search_query_from_history(question, history_pairs)
    try:
        _save_chat_event(
            claims,
            conversation_id=conv_id,
            role="meta",
            route="meta",
            message="",
            meta={
                "type": "query_refined",
                "original": question,
                "refined": effective_question,
                **refine_meta,
                "context": "vet_doc",
            },
        )
    except Exception:
        pass

    # 3) Search Azure sur l'index vétérinaire
    search_json = _search_vet_docs(effective_question, req.filters, k=VET_RETRIEVAL_K)
    hits = search_json.get("value", []) or []
    answers = search_json.get("@search.answers", []) or []

    if not _is_in_scope(hits) and not answers:
        payload = {
            "answer": "Je ne trouve pas d’information pertinente dans les documents vétérinaires pour cette question.",
            "citations": [],
            "used_docs": [],
            "conversation_id": conv_id,
            "images": [],
            "model": "Aïna Vet",
        }
        _save_chat_event(
            claims,
            conv_id,
            role="assistant",
            route="vet_doc",
            message=payload["answer"],
            meta=payload,
        )
        return payload

    # 4) Construction des contextes pour la synthèse Kimi
    N = max(1, min(req.top_k or VET_RETRIEVAL_K, TOPN_MAX))
    contexts: List[Dict[str, Any]] = []

    # 4-a) Réponses extractives Azure
    if answers:
        try:
            answers_sorted = sorted(answers, key=lambda a: a.get("score", 0), reverse=True)
        except Exception:
            answers_sorted = answers
        best_ans = answers_sorted[0]
        ans_text = (best_ans.get("text") or "").strip()
        if ans_text:
            contexts.append(
                {
                    "title": "Azure AI Search — Réponse",
                    "snippet": ans_text,
                    "meta": {
                        "kind": "answer",
                        "key": best_ans.get("key"),
                        "score": best_ans.get("score"),
                    },
                }
            )

    # 4-b) Documents
    for d in hits[:N]:
        doc_title = _extract_title_vet(d)
        doc_path = _extract_path_vet(d)
        snippet = _prefer_answer_or_focused_snippet(effective_question, d)
        contexts.append(
            {
                "title": doc_title,
                "snippet": snippet,
                "meta": {
                    "id": d.get("id"),
                    "path": doc_path,
                    "score": d.get("@search.score"),
                    "reranker": d.get("@search.rerankerScore"),
                },
            }
        )

    # 5) Synthèse RAG spécifique vet + Kimi
    answer_text, uses_context, used_list = _synthesize_vet_with_citations(
        question=question,
        contexts=contexts,
        chat_history_pairs=history_pairs,
    )

    def _is_doc_context(c: Dict[str, Any]) -> bool:
        return c.get("meta", {}).get("kind") != "answer"

    # 5-bis) used_docs
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

    # 6) Payload final (pas d'images dans ce flux)
    resp_payload = {
        "answer": answer_text,
        "citations": [],
        "used_docs": used_docs,
        "conversation_id": conv_id,
        "images": [],
        "model": "Aïna Vet",
    }

    _save_chat_event(
        claims,
        conv_id,
        role="assistant",
        route="vet_doc",
        message=resp_payload["answer"],
        meta={
            **resp_payload,
            "refined_query": effective_question,
            **refine_meta,
        },
    )

    return resp_payload
