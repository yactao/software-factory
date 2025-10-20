"""
Noyau d'orchestration et pipeline RAG.

Expose:
- Orchestrator: sélectionne l'agent, journalise les tours, exécute la requête.
- RagPipeline: utilitaires génériques retrieve → rank → synthesize.
- Types communs: AgentInput/Output, etc.
"""

from .orchestrator import Orchestrator
from .pipeline import RagPipeline
from .typing import (
    AgentInput,
    AgentOutput,
    RagContextDoc,
    SynthConfig,
)
