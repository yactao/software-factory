from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional, Tuple
import re
import unicodedata

from ..core.security import _auth_dependency, _require_scope
from ..core.config import RETRIEVAL_K, TOPN_MAX
from ..models.schemas import RAGRequest
from ..services.history_helpers import _save_chat_event, _get_last_qna_pairs
from ..services.search_azure import _search_docs
from ..services.gemini_rag import _synthesize_with_citations
from ..utils.snippets import (
    _extract_path,
    _extract_title,
    _is_in_scope,
    _make_used_doc_from_context,
    _prefer_answer_or_focused_snippet,
)
from ..utils.query_refiner import _compose_search_query_from_history

router = APIRouter()
SMALLTALK_RE = re.compile(r"^\s*(bonjour|bonsoir|salut|slt|hello|hi)\b", re.I)

def _norm(s: Optional[str]) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", s).strip().lower()

STORE_CODE_RE = re.compile(r"(^|[\s\-_/])(\d{2,6})(\b|$)")

def _extract_store_hints(question: str) -> Tuple[Optional[str], Optional[str]]:
    qn = _norm(question)

    m = STORE_CODE_RE.search(qn)
    code_hint = m.group(2) if m else None

    tmp = re.sub(r"\d{2,6}", " ", qn)
    tmp = re.sub(r"\b(magasin|photo|photos|images?|donne|moi|de|du|les|la|le|des|pour|mdm)\b", " ", tmp)
    name_hint = re.sub(r"[^a-z0-9\s\-]", " ", tmp)
    name_hint = re.sub(r"\s+", " ", name_hint).strip()

    if len(name_hint) < 3:
        name_hint = None

    return (name_hint, code_hint)

def _doc_matches_store(d: Dict[str, Any], name_hint: Optional[str], code_hint: Optional[str]) -> bool:
    name = _norm(d.get("magasin_name") or "")
    code = str(d.get("magasin_code") or "").strip()
    file_name = _norm(d.get("file_name") or "")

    ok = False
    if code_hint and code_hint and code == code_hint:
        ok = True

    if not ok and name_hint:
        tokens = [t for t in (name_hint or "").split() if len(t) >= 3]
        if tokens:
            if all(t in name for t in tokens) or all(t in file_name for t in tokens):
                ok = True

    return ok

def _gather_images_for_store(hits: List[Dict[str, Any]], name_hint: Optional[str], code_hint: Optional[str], limit: int) -> List[str]:
    images: List[str] = []
    for d in hits:
        if not _doc_matches_store(d, name_hint, code_hint):
            continue
        urls = d.get("image_blob_urls") or []
        if isinstance(urls, list):
            for u in urls:
                if isinstance(u, str) and u:
                    images.append(u)
        if len(images) >= limit:
            break
    seen = set()
    uniq = []
    for u in images:
        if u not in seen:
            uniq.append(u)
            seen.add(u)
    return uniq[:limit]

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

    # 1) Historique
    try:
        history_pairs = _get_last_qna_pairs(claims, conv_id, route="rag", max_pairs=3)
        if history_pairs and history_pairs[-1].get("user","").strip() == question:
            history_pairs = history_pairs[:-1]
    except Exception:
        history_pairs = []

    # 2) Raffinement
    effective_question, refine_meta = _compose_search_query_from_history(question, history_pairs)
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

    # 3) Search
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

    # 4) Contextes LLM
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
            "meta": {
                "id": d.get("id"),
                "path": doc_path,
                "score": d.get("@search.score"),
                "reranker": d.get("@search.rerankerScore"),
            },
        })

    # 5) Synthèse texte
    answer_text, uses_context, used_list = _synthesize_with_citations(
        question=question,
        contexts=contexts,
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

    # 6) Extraction images ciblées magasin
    name_hint, code_hint = _extract_store_hints(question)
    images: List[str] = []
    if name_hint or code_hint:
        # Limite d'images renvoyées (par défaut N, sinon 30)
        img_limit = max(1, min(req.top_k or 30, 200))
        images = _gather_images_for_store(hits, name_hint, code_hint, img_limit)

    # 7) Payload final
    final_answer = answer_text
    if images:
        # enrichir la réponse pour clarifier
        label = ""
        if code_hint and name_hint:
            label = f" pour « {name_hint} » (code {code_hint})"
        elif code_hint:
            label = f" pour le code {code_hint}"
        elif name_hint:
            label = f" pour « {name_hint} »"
        final_answer = f"J’ai trouvé {len(images)} image(s){label}."

    resp_payload = {
        "answer": final_answer,
        "citations": [],
        "used_docs": used_docs,
        "conversation_id": conv_id,
        "images": images,  
    }

    _save_chat_event(
        claims, conv_id, role="assistant", route="rag",
        message=resp_payload["answer"],
        meta={**resp_payload, "refined_query": effective_question, **refine_meta}
    )
    return resp_payload
