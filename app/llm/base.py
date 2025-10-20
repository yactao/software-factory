from __future__ import annotations
from typing import Protocol, Dict, Any


class LLMClient(Protocol):
    """
    Interface commune à tous les fournisseurs LLM.

    - generate_json: renvoie un objet JSON dict (avec fallbacks robustes côté client)
    - generate_text: renvoie un texte brut
    """

    def generate_json(self, prompt: str, sys: str, max_tokens: int, temperature: float) -> Dict[str, Any]:
        ...

    def generate_text(self, prompt: str, sys: str, max_tokens: int, temperature: float) -> str:
        ...
