# app/api/routes_finance.py

from fastapi import APIRouter, Depends, HTTPException
from typing import Any, Dict

from ..core.security import _auth_dependency, _require_scope
from ..models.schemas import FinanceRequest  # à définir
from ..services.history_helpers import _save_chat_event, _get_last_qna_pairs
from ..services.agent_finance import answer_finance_with_kimi

router = APIRouter()

@router.post("/api/aina/finance")
def finance(
    req: FinanceRequest,
    claims: Dict[str, Any] = Depends(_auth_dependency),
):
    _require_scope(claims)

    question = (req.question or "").strip()
    if not question:
        raise HTTPException(400, "Question vide.")

    conv_id = _save_chat_event(
        claims,
        req.conversation_id,
        role="user",
        route="finance",
        message=question,
        meta={},
    )

    try:
        history_pairs = _get_last_qna_pairs(claims, conv_id, route="finance", max_pairs=3)
        if history_pairs and history_pairs[-1].get("user", "").strip() == question:
            history_pairs = history_pairs[:-1]
    except Exception:
        history_pairs = []

    answer_text, chart = answer_finance_with_kimi(question, history_pairs)

    payload = {
        "answer": answer_text,
        "chart": chart,
        "conversation_id": conv_id,
    }

    _save_chat_event(
        claims,
        conv_id,
        role="assistant",
        route="finance",
        message=payload["answer"],
        meta=payload,
    )

    return payload
