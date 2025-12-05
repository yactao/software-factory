import json
from typing import List, Dict, Any, Tuple

from app.core.config import KIMI_MODEL_VET_DOC
from app.services.kimi_client import kimi_chat_completion


def _synthesize_vet_with_citations(
    question: str,
    contexts: List[Dict[str, Any]],
    chat_history_pairs: List[Dict[str, str]],
) -> Tuple[str, bool, List[int]]:
    """
    Synthèse RAG pour les documents vétérinaires via Kimi.
    Retourne (answer_text, uses_context, used_sources_indices)
    où used_sources_indices sont des indices 1-based dans contexts.
    """

    if not contexts:
        return (
            "Je ne trouve pas d'informations suffisantes dans les documents vétérinaires pour répondre précisément.",
            False,
            [],
        )

    # 1) SOURCES numérotées 1..N
    sources_block_lines = []
    for idx, c in enumerate(contexts, start=1):
        title = c.get("title") or f"Source {idx}"
        snippet = c.get("snippet") or ""
        sources_block_lines.append(f"[{idx}] {title}\n{snippet}")
    sources_block = "\n\n".join(sources_block_lines)

    # 2) Historique Q/A
    hist_lines = []
    for pair in chat_history_pairs[-3:]:
        u = pair.get("user", "").strip()
        a = pair.get("assistant", "").strip()
        if u:
            hist_lines.append(f"U: {u}")
        if a:
            hist_lines.append(f"A: {a}")
    history_text = "\n".join(hist_lines)

    # 3) Prompt système spécifique vétérinaire
    system_prompt = (
        "Tu es un assistant spécialisé pour un centre vétérinaire.\n"
        "Tu disposes de documents internes en français : procédures médicales, fiches diagnostiques,\n"
        "anesthésie, post-opératoire, urgences, gastro-entérite, intoxications, mais aussi RGPD,\n"
        "règlement intérieur, onboarding et fiches de poste.\n\n"
        "Règles STRICTES :\n"
        "1) Réponds UNIQUEMENT à partir des SOURCES fournies.\n"
        "2) Si une information n'est pas présente clairement dans les sources, dis-le explicitement\n"
        "   ('Les documents ne précisent pas ce point') et n'invente rien.\n"
        "3) Reste concis, structuré, et oriente la réponse comme un protocole ou des consignes pratiques.\n"
        "4) Langue : réponds en français.\n\n"
        "Format de sortie STRICTEMENT en JSON valide UTF-8, sans texte avant ni après.\n"
        "Les booléens doivent être true ou false sans guillemets.\n"
        "Schéma attendu :\n"
        "{\n"
        '  \"answer\": \"texte de la réponse\",\n'
        '  \"uses_context\": true,\n'
        '  \"used_sources\": [1, 2]\n'
        "}\n"
    )

    # 4) Prompt utilisateur
    user_prompt = (
        "QUESTION VETERINAIRE:\n"
        f"{question}\n\n"
        "CONTEXTE DE CONVERSATION RECENT (optionnel):\n"
        f"{history_text}\n\n"
        "SOURCES DISPONIBLES (procédures, diagnostics, RH, RGPD, etc.):\n"
        f"{sources_block}\n\n"
        "Réponds en JSON conforme au schéma demandé."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    # 5) Appel Kimi + parsing
    try:
        raw = kimi_chat_completion(
            messages,
            model=KIMI_MODEL_VET_DOC,
            temperature=0.1,
            max_tokens=1100,
        )
        raw_str = (raw or "").strip()

        # Tentative 1 : JSON direct
        try:
            obj = json.loads(raw_str)
        except Exception:
            # Tentative 2 : extraire { ... } s'il y a du bruit autour
            start = raw_str.find("{")
            end = raw_str.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    obj = json.loads(raw_str[start : end + 1])
                except Exception:
                    # Impossible de parser → renvoie texte brut
                    return raw_str, True, []
            else:
                return raw_str, True, []

    except Exception as e:
        return (
            f"Synthèse indisponible pour le moment. Détails: {e}",
            False,
            [],
        )

    # 6) Extraction des champs
    answer = (obj.get("answer") or "").strip()
    uses_context = bool(obj.get("uses_context", True))
    used_sources = obj.get("used_sources") or []

    used_indices: List[int] = []
    for i in used_sources:
        try:
            i_int = int(i)
        except Exception:
            continue
        if 1 <= i_int <= len(contexts):
            used_indices.append(i_int)

    if not answer:
        answer = "Réponse vide."

    return answer, uses_context, used_indices
