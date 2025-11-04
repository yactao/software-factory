import os, json, time, random
from typing import List, Dict, Any, Tuple
from fastapi import HTTPException
from ..core.config import (
    GEMINI_API_KEY, GEMINI_TEMPERATURE, GEMINI_MAX_OUTPUT_TOKENS,
    GEMINI_RETRIES, GEMINI_MODEL_CHAT
)
import google.generativeai as genai
from ..utils.text_clean import _clean_trading

def _configure_gemini_trading():
    """
    Modèle Gemini pour le domaine Trading.
    - Répond STRICTEMENT aux sources.
    - NE MET AUCUNE référence inline [n].
    - Produit un vrai résumé quand demandé.
    """
    if not GEMINI_API_KEY:
        raise HTTPException(500, "GEMINI_API_KEY non configurée.")
    genai.configure(api_key=GEMINI_API_KEY)

    rules = (
        "Tu es un assistant spécialisé trading pétrolier & conformité. "
        "Réponds STRICTEMENT aux SOURCES fournies; si l’info n’y est pas: dis 'Je ne sais pas'. "
        "Pas de conseils d’investissement personnalisés.\n\n"
        "Sortie: JSON STRICT uniquement (application/json) avec les champs: "
        '{"answer": "<texte brut, sans markdown, sans puces, sans emojis>", '
        '"uses_context": true|false, "used_sources": [<entiers 1..N>]}\n\n'
        "Style: phrases complètes, claires, en français si la question est en français. "
        "Pas de listes, pas de titres, pas de code, pas d’astérisques.\n\n"
        "Quand la question contient le mot 'résumé' ou 'synthèse', écris 150 à 220 mots "
        "couvrant: contexte, régulateurs (OFAC/UE/AML), obligations clés (KYC, screening, paiements, documentation), "
        "risques courants, bonnes pratiques. Sinon, réponds en 6–10 phrases selon le besoin."
    )

    model = genai.GenerativeModel(
        GEMINI_MODEL_CHAT,
        system_instruction=rules,
        generation_config={
            "temperature": GEMINI_TEMPERATURE,
            "max_output_tokens": max(GEMINI_MAX_OUTPUT_TOKENS, 900),
            "response_mime_type": "application/json",
        },
    )
    return model

def _trading_synthesize_with_citations(
    question: str,
    contexts: List[Dict[str, Any]],
    chat_history_text: str = ""
) -> Tuple[str, bool, List[int]]:
    try:
        model = _configure_gemini_trading()
    except Exception as e:
        return (f"Synthèse Trading indisponible: {e}", False, [])

    # Build sources block
    srcs = []
    for i, c in enumerate(contexts, 1):
        title = c.get("title") or c.get("file_name") or f"Source {i}"
        snippet = (c.get("snippet") or c.get("content") or "").strip()
        srcs.append(f"[{i}] {title}\n{snippet}")

    history = f"HISTORIQUE:\n{chat_history_text}\n\n" if chat_history_text else ""

    prompt = (
        history +
        f"QUESTION:\n{question}\n\n"
        "SOURCES (répond uniquement avec ces contenus):\n" +
        "\n\n".join(srcs)
    )

    for attempt in range(max(1, GEMINI_RETRIES)):
        try:
            resp = model.generate_content([{"role": "user", "parts": [{"text": prompt}]}])
            txt = (resp.text or "").strip()
            try:
                obj = json.loads(txt)
                answer = _clean_trading(obj.get("answer", ""))
                uses = bool(obj.get("uses_context", False))
                used = [int(x) for x in obj.get("used_sources", []) if str(x).isdigit()]
                return (answer, uses, used)
            except Exception:
                return (_clean_trading(txt), False, [])
        except Exception:
            if attempt < GEMINI_RETRIES - 1:
                time.sleep((2 ** attempt) + random.random())
                continue
            return ("Synthèse Trading indisponible.", False, [])
