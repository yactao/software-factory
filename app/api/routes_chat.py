from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.security.auth import require_user
from app.core import Orchestrator
from app.core.typing import AgentInput

router = APIRouter()


# --------- Schemas d'entrée ---------

class RAGBody(BaseModel):
    question: str
    filters: Optional[Dict[str, Any]] = None
    top_k: Optional[int] = 8
    conversation_id: Optional[str] = None
    index_name: Optional[str] = None


class SearchBody(BaseModel):
    prompt: str
    temperature: Optional[float] = None
    max_output_tokens: Optional[int] = None
    language: Optional[str] = None
    conversation_id: Optional[str] = None


# --------- RAG générique ---------

@router.post("/rag")
def rag_endpoint(body: RAGBody, claims=Depends(require_user)):
    q = (body.question or "").strip()
    if not q:
        raise HTTPException(400, "Question is empty.")
    orch = Orchestrator()
    req = AgentInput(
        question=q,
        claims=claims,
        route="rag",
        conversation_id=body.conversation_id,
        top_k=body.top_k or 8,
        filters=body.filters,
        index_name=body.index_name,
    )
    return orch.run(req).dict()


# --------- Trading ---------

@router.post("/trading")
def trading_endpoint(body: RAGBody, claims=Depends(require_user)):
    q = (body.question or "").strip()
    if not q:
        raise HTTPException(400, "Question is empty.")
    orch = Orchestrator()
    req = AgentInput(
        question=q,
        claims=claims,
        route="trading",
        conversation_id=body.conversation_id,
        top_k=body.top_k or 8,
        filters=body.filters,
        index_name=body.index_name,
    )
    return orch.run(req).dict()


# --------- HR ---------

@router.post("/hr")
def hr_endpoint(body: RAGBody, claims=Depends(require_user)):
    q = (body.question or "").strip()
    if not q:
        raise HTTPException(400, "Question is empty.")
    orch = Orchestrator()
    req = AgentInput(
        question=q,
        claims=claims,
        route="hr",
        conversation_id=body.conversation_id,
        top_k=body.top_k or 8,
        filters=body.filters,
        index_name=body.index_name,
    )
    return orch.run(req).dict()


# --------- Finance/Table ---------

@router.post("/finance")
def finance_endpoint(body: RAGBody, claims=Depends(require_user)):
    q = (body.question or "").strip()
    if not q:
        raise HTTPException(400, "Query is empty.")
    orch = Orchestrator()
    req = AgentInput(
        question=q,
        claims=claims,
        route="finance",
        conversation_id=body.conversation_id,
        top_k=min(max(body.top_k or 20, 1), 200),
        filters=body.filters,
        index_name=body.index_name,
    )
    return orch.run(req).dict()


# --------- Prompt-only (sans retrieval) ---------

@router.post("/search")
def search_prompt_only(body: SearchBody, claims=Depends(require_user)):
    prompt = (body.prompt or "").strip()
    if not prompt:
        raise HTTPException(400, "Le champ 'prompt' est requis et non vide.")
    # On réutilise l’orchestrateur avec route 'rag' et sans index spécifique :
    orch = Orchestrator()
    req = AgentInput(
        question=prompt,
        claims=claims,
        route="rag",
        conversation_id=body.conversation_id,
        top_k=1,
        filters={"__mode": "prompt_only"},  # indicateur libre si tu veux le traiter plus tard
    )
    return orch.run(req).dict()
