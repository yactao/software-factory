# app/routers/aina_trading_finance.py
"""
Route multi-Excel Aïna Trading Finance: analyse tous les .xlsx du container
FINANCE_CONTAINER. Même schéma de réponse que /api/aina/finance (answer, chart, rows)
avec doc_id sur chaque ligne.
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from ..core.security import _auth_dependency, _require_scope
from ..models.schemas import FinanceRequest
from ..services.history_helpers import _save_chat_event, _get_last_qna_pairs
from ..services.agent_trading_finance import answer_trading_finance_with_kimi

router = APIRouter()


@router.post("/api/aina/trading/finance")
def trading_finance(
    req: FinanceRequest,
    claims: Dict[str, Any] = Depends(_auth_dependency),
):
    """
    Aïna Trading Finance (multi-Excel).

    - Lit tous les fichiers .xlsx du container FINANCE_CONTAINER
    - Même flux que /api/aina/finance: question, historique, answer/chart/rows
    - Chaque élément de rows contient "doc_id" (nom du fichier source)
    """
    _require_scope(claims)

    question = (req.question or "").strip()
    if not question:
        raise HTTPException(400, "Question vide.")

    conv_id = _save_chat_event(
        claims,
        req.conversation_id,
        role="user",
        route="trading_finance",
        message=question,
        meta={},
    )

    try:
        history_pairs = _get_last_qna_pairs(
            claims,
            conv_id,
            route="trading_finance",
            max_pairs=3,
        )
        if history_pairs and history_pairs[-1].get("user", "").strip() == question:
            history_pairs = history_pairs[:-1]
    except Exception:
        history_pairs = []

    answer_text, chart, rows, columns = answer_trading_finance_with_kimi(question, history_pairs)

    payload: Dict[str, Any] = {
        "answer": answer_text,
        "chart": chart,
        "rows": rows,
        "columns": columns,
        "conversation_id": conv_id,
    }

    _save_chat_event(
        claims,
        conv_id,
        role="assistant",
        route="trading_finance",
        message=payload["answer"],
        meta=payload,
    )

    return payload
