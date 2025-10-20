from __future__ import annotations

import os
from typing import Optional

from fastapi import HTTPException

from app.llm.gemini_client import GeminiClient
from app.llm.openai_client import AzureOpenAIClient
from app.llm.deepseek_client import DeepSeekClient
from app.settings import get_settings


def get_llm(preferred: Optional[str] = None):
    """
    Retourne un client LLM selon le provider:
      - "gemini": GeminiClient (GEMINI_API_KEY)
      - "openai" / "azure" / "azureopenai": AzureOpenAIClient (endpoint+deployment)
      - "deepseek": DeepSeekClient (DEEPSEEK_API_KEY)
    """
    s = get_settings()
    name = (preferred or s.llm_provider or "gemini").lower()
    model = s.llm_model

    if name in ("openai", "azure", "azureopenai", "aoai", "azure-openai"):
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
        api_ver = os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01")
        api_key = os.getenv("AZURE_OPENAI_API_KEY") or s.openai_api_key  # backup si tu veux réutiliser ce champ
        return AzureOpenAIClient(endpoint=endpoint, deployment=deployment, api_version=api_ver, api_key=api_key)

    if name == "deepseek":
        # tu peux surcharger le modèle via s.llm_model si tu déploies deepseek-coder, etc.
        return DeepSeekClient(api_key=s.deepseek_api_key, model=model or "deepseek-chat")

    if name == "gemini":
        return GeminiClient(api_key=s.gemini_api_key, model=model or "gemini-1.5-flash")

    raise HTTPException(400, f"LLM provider inconnu: {name}")
