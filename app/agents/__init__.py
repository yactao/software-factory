"""
Agents de traitement spécialisés (RAG Doc, Trading, HR, Table/Finance, Vision).

Chaque agent:
- lit un historique de chat condensé de la même conversation
- construit le contexte (Azure Search si pertinent)
- appelle le LLM via app.llm.get_llm
- retourne AgentResult standardisé
"""

from .base import Agent, AgentRequest, AgentResult
from .agent_doc import DocAgent
from .agent_trading import TradingAgent
from .agent_hr import HrAgent
from .agent_table import TableAgent
from .agent_vision import VisionAgent

__all__ = [
    "Agent", "AgentRequest", "AgentResult",
    "DocAgent", "TradingAgent", "HrAgent", "TableAgent", "VisionAgent",
]
