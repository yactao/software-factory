from __future__ import annotations

from typing import Dict, Optional

from app.agents import (
    AgentRequest,
    AgentResult,
    DocAgent,
    TradingAgent,
    HrAgent,
    TableAgent,
    VisionAgent,
)
from app.core.typing import AgentInput, AgentOutput, SynthConfig
from app.settings import get_settings
from app.storage.tables import save_chat_event
from app.utils.text import clean_markdown


class Orchestrator:
    """
    Coeur d'orchestration:
    - Sélectionne l'agent selon la route ou les heuristiques simples.
    - Journalise dans Table Storage (tour user puis tour assistant).
    - Retourne un AgentOutput prêt pour les routes.
    """

    def __init__(self):
        s = get_settings()
        # mapping statique d'agents; extensible si besoin
        self._agents = {
            "rag": DocAgent(),
            "doc": DocAgent(),
            "trading": TradingAgent(),
            "hr": HrAgent(),
            "finance": TableAgent(),
            "vision": VisionAgent(),
        }
        self.default_route = "rag"

    # -------------------- Sélection d'agent --------------------

    def _guess_route(self, text: str) -> str:
        t = (text or "").lower()
        if any(k in t for k in ("contrat", "ofac", "vessel", "port", "cargo", "trading")):
            return "trading"
        if any(k in t for k in ("rh ", "ressources humaines", "congé", "policy", "benefits")):
            return "hr"
        if any(k in t for k in ("facture", "client", "tva", "écriture", "comptable", "journal")):
            return "finance"
        return self.default_route

    def _pick(self, route: Optional[str], text: str):
        r = (route or "").strip().lower() or self._guess_route(text)
        return self._agents.get(r, self._agents[self.default_route]), r

    # -------------------- Exécution --------------------

    def run(self, req: AgentInput) -> AgentOutput:
        """
        1) Log USER
        2) Dispatch agent
        3) Log ASSISTANT
        4) Retour AgentOutput
        """
        agent, route = self._pick(req.route, req.question)

        # Log USER
        conv_id = save_chat_event(
            claims=req.claims,
            conversation_id=req.conversation_id,
            role="user",
            route=route,
            message=req.question,
            meta={"filters": req.filters, "top_k": req.top_k, "index_name": req.index_name},
        )

        # Build AgentRequest (dataclass utilisée par nos agents)
        ar = AgentRequest(
            question=req.question,
            claims=req.claims,
            conversation_id=conv_id,
            top_k=max(1, min(req.top_k or 8, 50)),
            filters=req.filters,
            index_name=req.index_name,
        )

        # Call agent
        out: Dict = agent.handle(ar)

        # Log ASSISTANT (message uniquement)
        answer_text = clean_markdown(out.get("answer") or "")
        meta = dict(out)
        meta["type"] = "assistant_payload"
        save_chat_event(
            claims=req.claims,
            conversation_id=conv_id,
            role="assistant",
            route=route,
            message=answer_text[:32000],
            meta=meta,
        )

        # Norme AgentOutput
        return AgentOutput(
            answer=out.get("answer", ""),
            uses_context=bool(out.get("uses_context", False)),
            used_docs=out.get("used_docs", []),
            citations=out.get("citations", []),
            conversation_id=conv_id,
        )
