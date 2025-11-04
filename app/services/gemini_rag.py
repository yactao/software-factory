import json, time, random
from typing import List, Dict, Any, Tuple, Optional
from fastapi import HTTPException
from .gemini_base import _configure_gemini
from ..core.config import GEMINI_RETRIES
from ..utils.text_clean import _clean_model_text


def _synthesize_with_citations(
    question: str,
    contexts: List[Dict[str, Any]],
    chat_history_pairs: Optional[List[Dict[str, str]]] = None,
) -> Tuple[str, bool, List[int]]:
    """
    Version enrichie:
      - 'chat_history_pairs' contient jusqu'à 3 couples complets {"user","assistant"} de la même conversation.
      - L'historique est fourni au modèle DANS UNE SECTION DISTINCTE, à utiliser uniquement pour la continuité,
        JAMAIS comme source d'autorité. Les FAITS doivent venir des SOURCES.
    """
    try:
        model = _configure_gemini()
    except HTTPException:
        raise
    except Exception as e:
        return (f"Synthèse indisponible. Erreur de configuration Gemini: {e}", False, [])

    # Construire le bloc SOURCES numérotées (1..N)
    src_block: List[str] = []
    for i, c in enumerate(contexts, 1):
        title = c.get("title") or (c.get("meta", {}) or {}).get("path") or f"Source {i}"
        snippet = (c.get("snippet") or "")  # on n’écourte pas: on laisse tel quel
        src_block.append(f"[{i}] {title}\n{snippet}")

    # Construire le bloc HISTORIQUE strict (jusqu’à 3 couples complets U/A)
    hist_block = ""
    if chat_history_pairs:
        lines = ["HISTORIQUE DES 3 DERNIERS ECHANGES (NE PAS CONSIDERER COMME SOURCE D'AUTORITE)"]
        lines.append("Utilisation: uniquement pour la continuité (pronoms, ellipses). Les FAITS doivent provenir des SOURCES ci-dessous.")
        for idx, pair in enumerate(chat_history_pairs, 1):
            u = pair.get("user","")
            a = pair.get("assistant","")
            lines.append(f"--- PAIRE {idx} ---")
            lines.append(f"U: {u}")
            lines.append(f"A: {a}")
        hist_block = "\n".join(lines) + "\n\n"

    # Message utilisateur final: HISTORIQUE (si présent) puis QUESTION puis SOURCES
    user_msg = (
        (hist_block if hist_block else "") +
        f"QUESTION:\n{question}\n\n" +
        "SOURCES (les faits DOIVENT venir d'ici; ignorer l'historique en cas de contradiction):\n" +
        "\n\n".join(src_block)
    )

    # Appel modèle avec backoff simple
    for attempt in range(max(1, GEMINI_RETRIES)):
        try:
            resp = model.generate_content([{"role": "user", "parts": [{"text": user_msg}]}])
            txt = (resp.text or "").strip()
            try:
                obj = json.loads(txt)
                answer = _clean_model_text(str(obj.get("answer", "")).strip() or "Réponse vide.")
                uses_context = bool(obj.get("uses_context", False))
                used_sources = obj.get("used_sources") or []
                used_sources = [int(x) for x in used_sources if isinstance(x, (int, str)) and str(x).isdigit()]
                return (answer, uses_context, used_sources)
            except Exception:
                # Fallback texte brut
                txt = _clean_model_text(txt or "Synthèse indisponible.")
                return (txt, False, [])
        except Exception:
            if attempt < GEMINI_RETRIES - 1:
                time.sleep((2 ** attempt) + random.random())
                continue
            return ("Synthèse indisponible (Gemini).", False, [])
