# app/services/kimi_client.py

import os
from typing import List, Dict, Any

from fastapi import HTTPException
from openai import OpenAI

from app.core.config import MOONSHOT_API_KEY


def get_kimi_client() -> OpenAI:
    if not MOONSHOT_API_KEY:
        raise HTTPException(500, "MOONSHOT_API_KEY non configurée.")
    client = OpenAI(
        api_key=MOONSHOT_API_KEY,
        base_url="https://api.moonshot.ai/v1",
    )
    return client


def kimi_chat_completion(
    messages: List[Dict[str, Any]],
    model: str,
    temperature: float = 0.2,
    max_tokens: int = 2048,
) -> str:
    """
    Appel générique à Kimi en mode chat.completions.
    """
    client = get_kimi_client()
    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    msg = completion.choices[0].message

    # Gestion simple du contenu
    if isinstance(msg.content, str):
        return msg.content

    # Si c'est une liste de blocs, on concatène les textes
    parts = []
    for part in msg.content:
        if isinstance(part, dict) and part.get("type") in ("output_text", "text", "input_text"):
            parts.append(part.get("text", ""))
        elif isinstance(part, str):
            parts.append(part)
    return " ".join(parts).strip()
