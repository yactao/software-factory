from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Protocol, Optional


@dataclass
class AgentRequest:
    question: str
    claims: Dict[str, Any]
    conversation_id: Optional[str] = None
    top_k: int = 8
    filters: Optional[Dict[str, Any]] = None
    # index_name optionnel si tu veux surcharger côté route
    index_name: Optional[str] = None


@dataclass
class AgentResult:
    answer: str
    uses_context: bool
    used_docs: List[Dict[str, Any]]
    citations: List[Dict[str, Any]]
    conversation_id: Optional[str] = None


class Agent(Protocol):
    route_name: str  # ex: "rag", "trading", "hr", "finance", "vision"

    def handle(self, req: AgentRequest) -> AgentResult:
        ...
