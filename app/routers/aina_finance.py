# app/api/routes_finance.py

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from ..core.security import _auth_dependency, _require_scope
from ..models.schemas import FinanceRequest  # Pydantic model avec: question: str, conversation_id: str | None
from ..services.history_helpers import _save_chat_event, _get_last_qna_pairs
from ..services.agent_finance import answer_finance_with_kimi

router = APIRouter()


@router.post("/api/aina/finance")
def finance(
    req: FinanceRequest,
    claims: Dict[str, Any] = Depends(_auth_dependency),
):
    """
    Endpoint principal Aïna Finance.

    - Reçoit une question utilisateur (+ éventuellement conversation_id)
    - Sauvegarde l'événement "user"
    - Récupère l'historique des derniers échanges (Q/A)
    - Appelle l'agent Kimi pour analyser l'Excel finance
    - Sauvegarde l'événement "assistant"
    - Retourne:
        - answer: texte explicatif
        - chart: config du graphique
        - rows: extrait de lignes/colonnes utilisées
        - conversation_id: identifiant de la conversation
    """
    _require_scope(claims)

    question = (req.question or "").strip()
    if not question:
        raise HTTPException(400, "Question vide.")

    # 1) On enregistre le message utilisateur
    conv_id = _save_chat_event(
        claims,
        req.conversation_id,
        role="user",
        route="finance",
        message=question,
        meta={},
    )

    # 2) Historique des 3 derniers couples Q/A
    try:
        history_pairs = _get_last_qna_pairs(
            claims,
            conv_id,
            route="finance",
            max_pairs=3,
        )
        # Éviter de doubler la dernière question identique
        if history_pairs and history_pairs[-1].get("user", "").strip() == question:
            history_pairs = history_pairs[:-1]
    except Exception:
        history_pairs = []

    # 3) Appel à l'agent finance (Kimi) qui retourne answer, chart, excerpt_rows
    answer_text, chart, rows = answer_finance_with_kimi(question, history_pairs)

    # 4) Payload renvoyé au frontend (et stocké comme meta)
    payload: Dict[str, Any] = {
        "answer": answer_text,
        "chart": chart,
        "rows": rows,              # 🔥 extrait de lignes/colonnes pour FinanceTable
        "conversation_id": conv_id,
    }

    # 5) On enregistre la réponse assistant avec tout le meta (chart + rows)
    _save_chat_event(
        claims,
        conv_id,
        role="assistant",
        route="finance",
        message=payload["answer"],
        meta=payload,
    )

    return payload
