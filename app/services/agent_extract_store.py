# app/services/agent_extract_store.py

import json
from typing import List, Dict, Optional, Tuple

from app.core.config import KIMI_MODEL_SINGLE
from app.services.kimi_client import kimi_chat_completion


def extract_store_from_history_with_kimi(
    question: str,
    history_pairs: List[Dict[str, str]],
) -> Tuple[Optional[str], Optional[str]]:
    """
    Utilise Kimi pour extraire le nom du magasin et/ou le code magasin
    depuis la question actuelle ET l'historique de conversation.
    
    Retourne (name_hint, code_hint) où chaque valeur peut être None.
    """
    
    q = (question or "").strip()
    if not q:
        return None, None
    
    # Construire le contexte historique
    history_text = ""
    if history_pairs:
        history_lines = []
        for pair in history_pairs[-5:]:  # Derniers 5 échanges max
            user_msg = pair.get("user", "").strip()
            assistant_msg = pair.get("assistant", "").strip()
            if user_msg:
                history_lines.append(f"Utilisateur: {user_msg}")
            if assistant_msg:
                history_lines.append(f"Assistant: {assistant_msg[:200]}...")  # Limiter la longueur
        if history_lines:
            history_text = "\n".join(history_lines)
    
    system_prompt = (
        "Tu es un assistant qui extrait des informations sur les magasins depuis des conversations.\n"
        "Ton objectif est d'identifier :\n"
        "1) Le nom du magasin (ex: 'aix en provence', 'angers', 'ajaccio', 'paris', etc.)\n"
        "2) Le code magasin (ex: '06', '07', '08', '041', '142', etc.)\n\n"
        "IMPORTANT :\n"
        "- Si le nom du magasin ou le code est mentionné dans l'historique de conversation, tu dois l'utiliser.\n"
        "- Si la question actuelle demande des images sans mentionner explicitement le magasin, cherche dans l'historique.\n"
        "- Les noms de magasins sont souvent des villes ou des noms de lieux.\n"
        "- Les codes magasins sont des nombres (2 à 6 chiffres).\n"
        "- Si tu ne trouves rien, retourne null pour les valeurs manquantes.\n\n"
        "Réponds STRICTEMENT en JSON valide, sans texte avant ni après :\n"
        "{\n"
        '  "name": "nom_du_magasin" ou null,\n'
        '  "code": "code_magasin" ou null\n'
        "}"
    )
    
    user_prompt = ""
    if history_text:
        user_prompt = (
            "HISTORIQUE DE CONVERSATION :\n"
            f"{history_text}\n\n"
        )
    user_prompt += (
        "QUESTION ACTUELLE :\n"
        f"{q}\n\n"
        "Extrais le nom du magasin et/ou le code magasin depuis la question ET l'historique."
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    
    # Appel Kimi
    try:
        raw = kimi_chat_completion(
            messages,
            model=KIMI_MODEL_SINGLE,
            temperature=0.1,
            max_tokens=200,
        )
    except Exception as e:
        # En cas d'erreur, on retourne None, None
        return None, None
    
    raw_str = (raw or "").strip()
    
    # Parsing robuste du JSON
    try:
        obj = json.loads(raw_str)
    except Exception:
        # Tentative d'extraction du bloc JSON
        try:
            start = raw_str.find("{")
            end = raw_str.rfind("}")
            if start != -1 and end != -1 and end > start:
                cleaned = raw_str[start : end + 1]
                obj = json.loads(cleaned)
            else:
                return None, None
        except Exception:
            return None, None
    
    name_hint = obj.get("name")
    code_hint = obj.get("code")
    
    # Normaliser les valeurs
    if name_hint:
        name_hint = name_hint.strip() if isinstance(name_hint, str) else None
        if not name_hint or name_hint.lower() == "null":
            name_hint = None
    
    if code_hint:
        code_hint = str(code_hint).strip() if code_hint else None
        if not code_hint or code_hint.lower() == "null":
            code_hint = None
    
    return name_hint, code_hint

