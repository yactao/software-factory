from __future__ import annotations

from typing import Any, Dict, List, Tuple

from app.settings import get_settings


def _thresholds() -> Tuple[float, float]:
    """
    Lit les seuils par défaut (avec garde-fous) depuis settings ou valeurs standard.
    """
    # Valeurs par défaut raisonnables si non configurées:
    RERANKER_MIN_DEFAULT = 1.2
    BM25_MIN_DEFAULT = 1.0

    s = get_settings()
    # Si tu veux un contrôle plus fin par index, tu pourras lire config/indexes/*.yaml ici.
    reranker = RERANKER_MIN_DEFAULT
    bm25 = BM25_MIN_DEFAULT
    return float(reranker), float(bm25)


def in_scope(hits: List[Dict[str, Any]] | None, reranker_min: float | None = None, bm25_min: float | None = None) -> bool:
    """
    Détermine si la tête de résultats est suffisamment pertinente.
    Utilise @search.rerankerScore si présent, sinon @search.score (BM25).
    """
    if not hits:
        return False

    rmin, bmin = _thresholds()
    rmin = reranker_min if isinstance(reranker_min, (int, float)) else rmin
    bmin = bm25_min if isinstance(bm25_min, (int, float)) else bmin

    top = hits[0]
    rer = top.get("@search.rerankerScore")
    if isinstance(rer, (int, float)):
        return rer >= rmin
    scr = top.get("@search.score")
    if isinstance(scr, (int, float)):
        return scr >= bmin
    return False


def best_answers(search_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Renvoie les @search.answers triées par score décroissant si présentes.
    """
    answers = search_json.get("@search.answers", []) or []
    try:
        answers = sorted(answers, key=lambda a: a.get("score", 0), reverse=True)
    except Exception:
        pass
    return answers
