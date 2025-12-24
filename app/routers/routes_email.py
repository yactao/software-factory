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
    Endpoint AINA – Email Reader
    """
    _require_scope(claims)

    question = (req.question or "").strip()
    if not question:
        raise HTTPException(400, "Question vide.")

    # Sans OBO, on a besoin d’un token Graph fourni par le frontend
    graph_token = (req.graph_access_token or "").strip()
    if not graph_token:
        raise HTTPException(
            400,
            "graph_access_token manquant (token Microsoft Graph requis tant que OBO n'est pas implémenté)."
        )

    return answer_email_with_llm(
        question=question,
        graph_token=graph_token,
        claims=claims,
    
    )
