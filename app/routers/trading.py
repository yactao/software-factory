from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from ..core.security import _auth_dependency, _require_scope
from ..core.config import RETRIEVAL_K, TOPN_MAX
from ..models.schemas import TradingRequest
from ..services.history_helpers import TABLE_READY, _chat_table_cached, _pk_from_claims, _save_chat_event, _get_recent_chat_context
from ..services.search_azure import _search_trading_docs
from ..services.gemini_trading import _trading_synthesize_with_citations
from ..utils.snippets import _extract_title, _extract_path, _is_in_scope
import re

router = APIRouter()

SMALLTALK_RE = re.compile(r"^\s*(bonjour|bonsoir|salut|slt|hello|hi)\b", re.I)

@router.post("/api/trading")
def trading(req: TradingRequest, claims: Dict[str, Any] = Depends(_auth_dependency)):
    """
    /api/trading
    - Cherche dans l'index Trading (captions + contenu pour donner plus de contexte)
    - Injecte un historique condensé de la même conversation (U:/A:) pour la continuité
    - Synthèse via _trading_synthesize_with_citations (sans références inline)
    - Retourne 'answer' + 'used_docs' (citations inline proscrites)
    - Historisation Table Storage (route='trading')
    """
    _require_scope(claims)

    question = (req.question or "").strip()
    if not question:
        raise HTTPException(400, "Question is empty.")

    # 1) journal USER
    conv_id = _save_chat_event(
        claims,
        req.conversation_id,
        role="user",
        route="trading",
        message=question,
        meta={"filters": req.filters, "top_k": req.top_k}
    )

    # 2) petit garde-fou smalltalk
    if SMALLTALK_RE.search(question):
        payload = {
            "answer": "Bonjour. Posez une question liée à vos documents Trading pour que je puisse répondre.",
            "citations": [],
            "used_docs": [],
            "conversation_id": conv_id,
        }
        _save_chat_event(claims, conv_id, role="assistant", route="trading",
                         message=payload["answer"], meta=payload)
        return payload

    # 3) récupérer un court historique de la même conversation (continuité du chat)
    chat_history_text = ""
    try:
        table = _chat_table_cached()
        if table is not None and TABLE_READY and conv_id:
            pk = _pk_from_claims(claims)
            # On récupère les messages (user/assistant) de CETTE conversation
            items = list(table.query_entities(
                query_filter=f"PartitionKey eq '{pk}' and conversation_id eq '{conv_id}'",
                select=["RowKey","role","route","message"]
            ))
            # tri chrono par RowKey
            items.sort(key=lambda x: x.get("RowKey",""))
            # On garde les derniers tours (avant la réponse en cours) et seulement route='trading'
            turns = []
            for it in items:
                if (it.get("route") == "trading") and (it.get("role") in ("user","assistant")):
                    msg = (it.get("message") or "").strip()
                    if not msg:
                        continue
                    turns.append(("U" if it.get("role") == "user" else "A", msg))
            # On ne veut pas dépasser ~1000-1500 caractères pour le contexte d'historique
            # On prend les 6 derniers échanges max (12 lignes U:/A:)
            trimmed = turns[-12:]
            # Format "U: ...\nA: ..."
            chat_history_text = "\n".join([f"{speaker}: {text}" for speaker, text in trimmed])
            # On évite de répéter la toute dernière ligne U: si c'est la question qu'on vient d'ajouter
            if chat_history_text.endswith(f"U: {question}"):
                # retire la dernière ligne
                chat_history_lines = chat_history_text.splitlines()
                chat_history_text = "\n".join(chat_history_lines[:-1])
            # Soft cap sur la taille
            if len(chat_history_text) > 1500:
                chat_history_text = chat_history_text[-1500:]
    except Exception:
        # Historique facultatif : on ignore silencieusement en cas de souci
        chat_history_text = ""

    # 4) recherche candidats (index Trading)
    search_json = _search_trading_docs(question, req.filters, k=RETRIEVAL_K)
    hits = search_json.get("value", []) or []

    if not _is_in_scope(hits):
        payload = {
            "answer": "Je ne sais pas. Aucune information suffisamment pertinente dans les documents indexés.",
            "citations": [],
            "used_docs": [],
            "conversation_id": conv_id,
        }
        _save_chat_event(claims, conv_id, role="assistant", route="trading",
                         message=payload["answer"], meta=payload)
        return payload

    # 5) construire le contexte (CAPTION + début du CONTENU pour + de matière)
    N = max(1, min(req.top_k or TOPN_MAX, TOPN_MAX))
    contexts: List[Dict[str, Any]] = []
    for d in hits[:N]:
        doc_title = _extract_title(d)
        doc_path = d.get("source_path") or _extract_path(d)

        caps = d.get("@search.captions") or []
        cap_text = caps[0].get("text") if caps else ""
        content_text = (d.get("content") or "")
        # Concat : caption + contenu (fenêtre élargie)
        snippet = (cap_text + "\n" + content_text)[:1800]

        contexts.append({
            "title": doc_title,
            "snippet": snippet,
            "meta": {
                "score": d.get("@search.score"),
                "reranker": d.get("@search.rerankerScore"),
                "path": doc_path,
                "id": d.get("id"),
            },
        })

    if not contexts:
        payload = {
            "answer": "Je ne sais pas. Aucun contexte exploitable n'a été trouvé.",
            "citations": [],
            "used_docs": [],
            "conversation_id": conv_id,
        }
        _save_chat_event(claims, conv_id, role="assistant", route="trading",
                         message=payload["answer"], meta=payload)
        return payload

    # 6) synthèse (modèle trading, sortie JSON → answer nettoyée sans [n])
    answer, uses_context, used_list = _trading_synthesize_with_citations(
        question=question,
        contexts=contexts,
        chat_history_text=chat_history_text
    )

    # 7) assembler used_docs (pas de citations inline)
    citations: List[Dict[str, Any]] = []  # champ conservé pour le front (vide)

    if used_list:
        selected = [contexts[i - 1] for i in used_list if 1 <= i <= len(contexts)]
        used_docs = [{
            "id": c.get("meta", {}).get("id"),
            "title": c.get("title") or (c.get("meta", {}).get("path") or "Document"),
            "path": c.get("meta", {}).get("path"),
            "score": c.get("meta", {}).get("score"),
            "reranker": c.get("meta", {}).get("reranker"),
        } for c in selected]
    elif uses_context:
        selected = contexts[: min(3, len(contexts))]
        used_docs = [{
            "id": c.get("meta", {}).get("id"),
            "title": c.get("title") or (c.get("meta", {}).get("path") or "Document"),
            "path": c.get("meta", {}).get("path"),
            "score": c.get("meta", {}).get("score"),
            "reranker": c.get("meta", {}).get("reranker"),
        } for c in selected]
    else:
        used_docs = []

    # 8) réponse + log assistant
    resp_payload = {
        "answer": answer,
        "citations": citations,     # volontairement vide (pas de [n] dans le texte)
        "used_docs": used_docs,     # docs réellement utilisés/montrés
        "conversation_id": conv_id,
    }
    _save_chat_event(claims, conv_id, role="assistant", route="trading",
                     message=answer, meta=resp_payload)

    return resp_payload
