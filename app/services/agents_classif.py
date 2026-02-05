# app/services/agents_classif.py

import json
from typing import Literal, Tuple

from fastapi import HTTPException

from app.services.llm_provider import llm_chat_completion

ScopeType = Literal["single_store", "global", "fallback"]


def decide_scope_with_kimi(question: str) -> Tuple[ScopeType, str]:
    """
    Le LLM décide SANS heuristique locale :
      - "single_store"
      - "global"
      - "fallback"

    Sortie demandée STRICTEMENT en JSON.
    Parsing robuste pour éviter les erreurs "Unterminated string".
    """

    q = (question or "").strip()
    if not q:
        return "fallback", "empty_question"

    system_prompt = (
        "Tu es un classifieur pour un assistant d'audit de magasins.\n"
        "Ton objectif est de dire si la question concerne :\n"
        "1) un magasin précis (scope = \"single_store\")\n"
        "2) tous les magasins, l'ensemble du parc (scope = \"global\")\n"
        "3) ou si ce n'est pas clair (scope = \"fallback\")\n\n"
        "Critères :\n"
        "- Si la question demande un comparatif, une moyenne, un classement, une synthèse sur plusieurs magasins : scope = \"global\".\n"
        "- Si la question cible un magasin, un code magasin, une fiche spécifique : scope = \"single_store\".\n"
        "- Si c'est ambigu ou pas clair : scope = \"fallback\".\n\n"
        "Réponds STRICTEMENT en JSON valide, sans texte avant ni après :\n"
        "{\n"
        '  \"scope\": \"single_store\" ou \"global\" ou \"fallback\",\n'
        '  \"reason\": \"texte explicatif\"\n'
        "}"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": q},
    ]

    try:
        raw = llm_chat_completion(
            "rag_classif",
            messages,
            temperature=0.0,
            max_tokens=300,
        )
    except Exception as e:
        return "fallback", f"llm_api_error:{e}"

    raw_str = (raw or "").strip()

    # ==============================
    # 🔥 PARSING ROBUSTE DU JSON
    # ==============================

    # 1. Tentative directe
    try:
        return _parse_decision_json(raw_str)
    except Exception:
        pass

    # 2. Extraction du bloc { ... } s'il y a du bruit autour
    try:
        start = raw_str.find("{")
        end = raw_str.rfind("}")
        if start != -1 and end != -1 and end > start:
            cleaned = raw_str[start : end + 1]
            return _parse_decision_json(cleaned)
    except Exception:
        pass

    # 3. Dernier recours : renvoyer fallback sans casser
    return "fallback", "cannot_parse_json"


# Fonction utilitaire interne
def _parse_decision_json(txt: str) -> Tuple[ScopeType, str]:
    obj = json.loads(txt)

    scope = obj.get("scope", "").strip()
    reason = obj.get("reason", "").strip() or "no_reason"

    if scope not in ("single_store", "global", "fallback"):
        return "fallback", "invalid_scope_value"

    return scope, reason
