# app/api/routes_vet_finance.py

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from ..core.security import _auth_dependency, _require_scope
from ..models.schemas import VetFinanceRequest
from ..services.history_helpers import _save_chat_event, _get_last_qna_pairs
from ..services.agent_vet_finance import answer_vet_finance_with_kimi

router = APIRouter()


@router.post("/api/vet/finance")
def vet_finance(
    req: VetFinanceRequest,
    claims: Dict[str, Any] = Depends(_auth_dependency),
):
    """
    Endpoint principal Vet Finance.

    Fonctionnement:
      1) Reçoit une question plus éventuellement un conversation_id
      2) Sauvegarde le message utilisateur dans l historique
      3) Récupère les derniers couples question réponse pour le contexte
      4) Appelle l agent vet finance qui analyse le fichier Excel tri feuilles
      5) Sauvegarde la réponse assistant dans l historique
      6) Retourne answer, chart, rows et conversation_id
    """
    _require_scope(claims)

    question = (req.question or "").strip()
    if not question:
        raise HTTPException(400, "Question vide.")

    # 1) Enregistrement du message utilisateur
    conv_id = _save_chat_event(
        claims,
        req.conversation_id,
        role="user",
        route="vet_finance",
        message=question,
        meta={},
    )

    # 2) Historique des 3 derniers couples Q A
    try:
        history_pairs = _get_last_qna_pairs(
            claims,
            conv_id,
            route="vet_finance",
            max_pairs=3,
        )
        if history_pairs and history_pairs[-1].get("user", "").strip() == question:
            history_pairs = history_pairs[:-1]
    except Exception:
        history_pairs = []

    # 3) Appel de l agent Vet Finance
    answer_text, chart, rows = answer_vet_finance_with_kimi(question, history_pairs)

    payload: Dict[str, Any] = {
        "answer": answer_text,
        "chart": chart,
        "rows": rows,
        "conversation_id": conv_id,
    }

    # 4) Enregistrement de la réponse assistant avec le meta complet
    _save_chat_event(
        claims,
        conv_id,
        role="assistant",
        route="vet_finance",
        message=payload["answer"],
        meta=payload,
    )

    return payload
