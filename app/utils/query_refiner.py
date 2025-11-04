import json, time, random
import google.generativeai as genai
from typing import Tuple
from ..core.config import GEMINI_API_KEY, GEMINI_MODEL_CHAT, GEMINI_RETRIES
from fastapi import HTTPException


def _configure_gemini_query_refiner():
    if not GEMINI_API_KEY:
        raise HTTPException(500, "GEMINI_API_KEY non configurée.")
    genai.configure(api_key=GEMINI_API_KEY)

    model_id = GEMINI_MODEL_CHAT
    return genai.GenerativeModel(
        model_id,
        system_instruction=(
            "Tu reçois une QUESTION et jusqu'à 3 couples exacts d'historique (U/A). "
            "Ta tâche: produire une version COMPLÈTE et NON AMBIGUË de la question POUR LA RECHERCHE DOCUMENTAIRE. "
            "Tu peux uniquement combler les éléments elliptiques (ex: 'cette intervention', pronoms, dates implicites) "
            "en t'appuyant strictement sur l'historique, sans rien inventer. "
            "Si l'historique ne permet pas d'être certain, renvoie la question originale. "
            "Ne pas résumer, ne pas paraphraser inutilement: juste compléter. "
            "Sortie JSON STRICT:\n"
            "{\n"
            '  "query": "<question à envoyer à Azure Search>",\n'
            '  "used_history": true|false,\n'
            '  "reason": "<brève justification lisible par un humain>"\n'
            "}\n"
        ),
        generation_config={
            "temperature": 0.1,
            "max_output_tokens": 256,
            "response_mime_type": "application/json",
        },
    )

def _compose_search_query_from_history(
    question: str,
    chat_history_pairs: list[dict]
) -> tuple[str, dict]:
    """
    Retourne (query_effective, meta) où:
      - query_effective: requête finale pour Azure Search (question complétée si possible)
      - meta: {"used_history": bool, "reason": str}
    Si pas d'historique ou erreur → renvoie (question, {"used_history": False, "reason": "as_is"}).
    """
    q = (question or "").strip()
    if not q:
        return q, {"used_history": False, "reason": "empty"}

    # Pas d'historique → on garde tel quel
    if not chat_history_pairs:
        return q, {"used_history": False, "reason": "no_history"}

    # Construire bloc HISTORIQUE exact (sans résumé)
    lines = []
    for idx, pair in enumerate(chat_history_pairs[-3:], 1):
        u = pair.get("user", "")
        a = pair.get("assistant", "")
        lines.append(f"--- PAIRE {idx} ---")
        lines.append(f"U: {u}")
        lines.append(f"A: {a}")
    hist_block = "\n".join(lines)

    prompt = (
        "QUESTION:\n" + q + "\n\n" +
        "DERNIERS ECHANGES (EXACTS, SANS RESUME):\n" +
        hist_block
    )

    try:
        model = _configure_gemini_query_refiner()
        resp = model.generate_content([{"role": "user", "parts": [{"text": prompt}]}])
        raw = (resp.text or "").strip()
        obj = json.loads(raw)
        query = (obj.get("query") or "").strip()
        used_history = bool(obj.get("used_history", False))
        reason = (obj.get("reason") or "").strip()

        if not query:
            return q, {"used_history": False, "reason": "fallback_empty_query"}

        # Si le refiner renvoie exactement la même question, on note as_is
        if query == q:
            return q, {"used_history": used_history, "reason": reason or "as_is"}

        return query, {"used_history": used_history, "reason": reason or "completed_from_history"}

    except Exception:
        return q, {"used_history": False, "reason": "refiner_error_as_is"}
