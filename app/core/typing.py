from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RagContextDoc(BaseModel):
    """Item de contexte passé au LLM (titre + extrait + méta pour citations UI)."""
    title: str = Field(default="Document")
    snippet: str = Field(default="")
    meta: Dict[str, Any] = Field(default_factory=dict)


class SynthConfig(BaseModel):
    """Configuration de synthèse commune (LLM, tokens, température, règles)."""
    provider: Optional[str] = None        # gemini | openai (azure) | deepseek
    model: Optional[str] = None
    temperature: float = 0.2
    max_output_tokens: int = 900
    system_rules: Optional[str] = None    # prompt système si nécessaire


class AgentInput(BaseModel):
    """Entrée normalisée pour l’orchestrateur/agents."""
    question: str
    claims: Dict[str, Any]                 # JWT claims (pour tenant/user)
    route: str = "rag"                     # rag | trading | hr | finance | vision
    conversation_id: Optional[str] = None
    top_k: int = 8
    filters: Optional[Dict[str, Any]] = None
    index_name: Optional[str] = None       # pour surcharger l’index par route


class AgentOutput(BaseModel):
    """Sortie normalisée d’un agent."""
    answer: str
    uses_context: bool = False
    used_docs: List[Dict[str, Any]] = []
    citations: List[Dict[str, Any]] = []
    conversation_id: Optional[str] = None
