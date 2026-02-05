# app/services/llm_provider.py
"""
Abstraction LLM pour RAG et Aïna Finance.
Permet de choisir le fournisseur (Kimi, OpenAI, Azure OpenAI) via la config.
"""

from typing import Any, Dict, List, Tuple, Union

from fastapi import HTTPException
from openai import OpenAI, AzureOpenAI

from app.core.config import (
    RAG_LLM_PROVIDER,
    FINANCE_LLM_PROVIDER,
    RAG_MODEL_SINGLE,
    RAG_MODEL_GLOBAL,
    RAG_MODEL_CLASSIF,
    FINANCE_MODEL,
    OPENAI_API_KEY,
    MOONSHOT_API_KEY,
    AZURE_OAI_ENDPOINT,
    AZURE_OAI_KEY,
    AZURE_OAI_DEPLOYMENT,
    RAG_AZURE_DEPLOYMENT,
    RAG_GLOBAL_AZURE_DEPLOYMENT,
    FINANCE_AZURE_DEPLOYMENT,
)

# Use case = rag_single | rag_global | rag_classif | finance
USE_CASES = ("rag_single", "rag_global", "rag_classif", "finance")


def _get_kimi_client() -> OpenAI:
    if not MOONSHOT_API_KEY:
        raise HTTPException(500, "MOONSHOT_API_KEY non configurée.")
    return OpenAI(
        api_key=MOONSHOT_API_KEY,
        base_url="https://api.moonshot.ai/v1",
    )


def _get_openai_client() -> OpenAI:
    if not OPENAI_API_KEY:
        raise HTTPException(500, "OPENAI_API_KEY non configurée pour le provider openai.")
    return OpenAI(api_key=OPENAI_API_KEY)


def _get_azure_openai_client() -> AzureOpenAI:
    if not AZURE_OAI_ENDPOINT or not AZURE_OAI_KEY:
        raise HTTPException(500, "AZURE_OAI_ENDPOINT et AZURE_OAI_KEY requis pour azure_openai.")
    return AzureOpenAI(
        azure_endpoint=AZURE_OAI_ENDPOINT,
        api_key=AZURE_OAI_KEY,
        api_version="2024-08-01-preview",
    )


def get_llm_client(provider: str):
    """Retourne le client OpenAI/AzureOpenAI pour le provider donné."""
    p = (provider or "kimi").strip().lower()
    if p == "kimi":
        return _get_kimi_client()
    if p == "openai":
        return _get_openai_client()
    if p == "azure_openai":
        return _get_azure_openai_client()
    raise HTTPException(500, f"Provider LLM inconnu: {provider}")


def _rag_model(use_case: str) -> str:
    if use_case == "rag_single":
        return RAG_MODEL_SINGLE
    if use_case == "rag_global":
        return RAG_MODEL_GLOBAL
    if use_case == "rag_classif":
        return RAG_MODEL_CLASSIF
    return RAG_MODEL_SINGLE


def _azure_deployment(use_case: str) -> str:
    d = AZURE_OAI_DEPLOYMENT or ""
    if use_case == "rag_single" and RAG_AZURE_DEPLOYMENT:
        return RAG_AZURE_DEPLOYMENT
    if use_case == "rag_global" and RAG_GLOBAL_AZURE_DEPLOYMENT:
        return RAG_GLOBAL_AZURE_DEPLOYMENT
    if use_case == "finance" and FINANCE_AZURE_DEPLOYMENT:
        return FINANCE_AZURE_DEPLOYMENT
    if use_case in ("rag_single", "rag_global", "rag_classif") and RAG_AZURE_DEPLOYMENT:
        return RAG_AZURE_DEPLOYMENT
    return d


def get_llm_client_and_model(use_case: str) -> Tuple[Any, str]:
    """
    Retourne (client, model_name) pour le use_case donné.
    use_case in: rag_single, rag_global, rag_classif, finance
    """
    if use_case not in USE_CASES:
        raise HTTPException(500, f"Use case inconnu: {use_case}")
    if use_case == "finance":
        provider = FINANCE_LLM_PROVIDER
        if provider == "azure_openai":
            return get_llm_client(provider), _azure_deployment("finance") or FINANCE_MODEL
        return get_llm_client(provider), FINANCE_MODEL
    provider = RAG_LLM_PROVIDER
    if provider == "azure_openai":
        return get_llm_client(provider), _azure_deployment(use_case) or _rag_model(use_case)
    return get_llm_client(provider), _rag_model(use_case)


def _normalize_message_content(content: Union[str, List[Any]]) -> List[Dict[str, Any]]:
    """Convertit les messages en format attendu par l'API (liste de dicts avec role et content)."""
    normalized = []
    for m in content:
        if isinstance(m, dict):
            role = m.get("role")
            c = m.get("content")
            if isinstance(c, list):
                normalized.append({"role": role, "content": c})
            else:
                normalized.append({"role": role, "content": c or ""})
        else:
            normalized.append(m)
    return normalized


def _extract_text_from_response(msg: Any) -> str:
    """Extrait le texte de la réponse (string ou liste de blocs type Kimi/OpenAI)."""
    content = getattr(msg, "content", msg) if not isinstance(msg, dict) else msg.get("content")
    if isinstance(content, str):
        return content.strip()
    if not content:
        return ""
    parts = []
    for part in content:
        if isinstance(part, dict):
            if part.get("type") in ("output_text", "text", "input_text"):
                parts.append(part.get("text", ""))
            elif "text" in part:
                parts.append(part["text"])
        elif isinstance(part, str):
            parts.append(part)
    return " ".join(parts).strip()


def llm_chat_completion(
    use_case: str,
    messages: List[Dict[str, Any]],
    temperature: float = 0.2,
    max_tokens: int = 2048,
) -> str:
    """
    Appel chat completion avec le client et le modèle configurés pour ce use_case.
    Retourne le texte de la réponse.
    """
    client, model = get_llm_client_and_model(use_case)
    messages = _normalize_message_content(messages)
    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    msg = completion.choices[0].message
    return _extract_text_from_response(msg)


def llm_chat_completion_with_client(
    client: Any,
    model: str,
    messages: List[Dict[str, Any]],
    temperature: float = 0.2,
    max_tokens: int = 2048,
) -> str:
    """Appel chat completion avec un client et un modèle déjà choisis."""
    messages = _normalize_message_content(messages)
    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    msg = completion.choices[0].message
    return _extract_text_from_response(msg)
