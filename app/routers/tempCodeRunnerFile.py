# app/routers/routes_email.py

from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException

from app.core.security import _auth_dependency, _require_scope
from app.models.schemas import EmailRequest
from app.services.agent_email import answer_email_with_llm

router = APIRouter()

@router.post("/api/aina/email")
def email_agent(
    req: EmailRequest,
    claims: Dict[str, Any] = Depends(_auth_dependency),
):
    """
    Endpoint AINA – Email Reader (OBO)
    """
    _require_scope(claims)

    question = (req.question or "").strip()
    if not question:
        raise HTTPException(400, "Question vide.")

    # ✅ OBO → plus besoin de graph_access_token
    return answer_email_with_llm(
        question=question,
        claims=claims,
    )
