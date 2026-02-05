import json
from typing import List, Dict, Any, Tuple

from app.services.llm_provider import llm_chat_completion


def _synthesize_with_citations(
    question: str,
    contexts: List[Dict[str, Any]],
    chat_history_pairs: List[Dict[str, str]],
) -> Tuple[str, bool, List[int]]:
    """
    Synthèse RAG via Kimi (single fiche).
    Retourne (answer_text, uses_context, used_sources_indices)
    où used_sources_indices sont des indices 1-based dans contexts.
    """

    if not contexts:
        return (
            "Je ne trouve pas d'informations suffisantes dans les documents pour répondre précisément.",
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

    # 2) Historique
    hist_lines = []
    for pair in chat_history_pairs[-3:]:
        u = pair.get("user", "").strip()
        a = pair.get("assistant", "").strip()
        if u:
            hist_lines.append(f"U: {u}")
        if a:
            hist_lines.append(f"A: {a}")
    history_text = "\n".join(hist_lines)

    # 3) Prompt système Kimi
    system_prompt = (
        "Tu es un assistant d'entreprise pour un système RAG basé sur des fiches d'audit.\n"
        "Tu dois répondre EXCLUSIVEMENT à partir des SOURCES fournies.\n"
        "Si une information ne figure pas dans les sources, dis-le et n'invente rien.\n\n"
        "Langue: réponds dans la langue de la question.\n\n"
        "Format de sortie STRICTEMENT en JSON valide UTF-8, sans texte avant ni après.\n"
        "Les booléens doivent être true ou false sans guillemets.\n"
        "Exemple de structure attendue:\n"
        "{\n"
        '  \"answer\": \"texte de la réponse\",\n'
        '  \"uses_context\": true,\n'
        '  \"used_sources\": [1, 2, 3]\n'
        "}\n"
    )

    # 4) Prompt utilisateur
    user_prompt = (
        "QUESTION UTILISATEUR:\n"
        f"{question}\n\n"
        "DERNIER CONTEXTE DE CONVERSATION (optionnel):\n"
        f"{history_text}\n\n"
        "SOURCES DISPONIBLES:\n"
        f"{sources_block}\n\n"
        "Réponds en JSON conforme au schéma demandé."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    # 5) Appel LLM (Kimi / OpenAI / Azure) + parsing robuste
    try:
        raw = llm_chat_completion(
            "rag_single",
            messages,
            temperature=0.1,
            max_tokens=1100,
        )
        raw_str = (raw or "").strip()

        # Tentative 1: JSON direct
        try:
            obj = json.loads(raw_str)
        except Exception:
            # Tentative 2: extraire le bloc { ... } s'il y a du bruit autour
            start = raw_str.find("{")
            end = raw_str.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    obj = json.loads(raw_str[start : end + 1])
                except Exception:
                    # Tentative 3: fallback texte brut sans citations
                    return raw_str, True, []
            else:
                # Pas de JSON exploitable → on renvoie le texte brut
                return raw_str, True, []

    except Exception as e:
        # Vrai problème réseau / API → message d'erreur
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
