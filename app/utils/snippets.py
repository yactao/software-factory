import re, unicodedata
from typing import Dict, Any, List, Optional
from ..core.config import RERANKER_MIN, BM25_MIN
from .text_clean import _MD_BOLD_RE, _MD_ITALIC_RE, _MD_HEADERS_RE  # si besoin

_STOPWORDS_FR = {
    "le","la","les","de","des","du","un","une","au","aux","pour","par","sur","dans","avec",
    "et","ou","que","qui","quoi","dont","où","a","à","au","aux","en","d","l","s","ce","cet","cette",
    "donne","donner","donnez","moi","me","mon","ma","mes","ton","ta","tes","son","sa","ses","est","être",
    "intervention","interventions","descriptif","descriptifs","type","client","ville","date","procès-verbal"
}
# ============================================================
# Normalisation textuelle pour matching
# ============================================================

def _normalize_for_match(s: str) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s

# ============================================================
# Extraction des termes de requête
# ============================================================

def _extract_query_terms(q: str, min_len: int = 3) -> list[str]:
    """
    Tire des termes discriminants depuis la question:
      - nombres longs et id du style 24001175-24604
      - mots alphanum >= min_len, stopwords exclus
    """
    qn = _normalize_for_match(q.lower())
    ids = re.findall(r"\b\d{5,}-\d{3,}\b", qn)  
    nums = re.findall(r"\b\d{4,}\b", qn)       # années, refs longues
    words = re.findall(r"[a-z0-9]{%d,}" % min_len, qn)
    words = [w for w in words if w not in _STOPWORDS_FR]
    terms = list(dict.fromkeys(ids + nums + words))  # dédup ordre
    return terms[:20]  # cap


# ============================================================
# Score local d'un segment textuel
# ============================================================

def _score_text_span(txt_norm: str, terms: list[str]) -> int:
    """
    Score simple: somme des occurrences de chaque terme.
    Bonus si plusieurs termes apparaissent rapprochés.
    """
    if not terms:
        return 0
    score = 0
    for t in terms:
        score += txt_norm.count(t)
    # bonus proximité: si au moins 2 termes dans 120 caractères
    if len(terms) >= 2:
        pattern = r"(" + r"|".join(map(re.escape, terms)) + r")"
        hits = [m.start() for m in re.finditer(pattern, txt_norm)]
        for i in range(len(hits) - 1):
            if hits[i+1] - hits[i] <= 120:
                score += 1
    return score


# ============================================================
# Trouver la meilleure fenêtre (snippet focalisé)
# ============================================================
def _best_window(text: str, terms: list[str], window: int = 1400, step: int = 350) -> str:
    """
    Cherche la fenêtre la mieux scorée en glissant avec un pas 'step'.
    On matche en version normalisée, on renvoie le texte original.
    """
    if not text:
        return ""
    if len(text) <= window:
        return text

    tnorm = _normalize_for_match(text.lower())
    best = (0, 0)  # (score, start)
    n = len(text)
    # balayage
    pos = 0
    while pos < n:
        end = min(n, pos + window)
        slice_norm = tnorm[pos:end]
        sc = _score_text_span(slice_norm, terms)
        if sc > best[0]:
            best = (sc, pos)
        pos += step

    # si tout a score nul, renvoyer tête
    start = best[1] if best[0] > 0 else 0
    out = text[start:start + window].strip()
    # cap de sécurité
    return out[:1600]


# ============================================================
# Préférer une réponse directe ou un snippet informatif
# ============================================================

def _prefer_answer_or_focused_snippet(question: str, d: dict) -> str:
    """
    Utilise @search.captions pour amorcer, puis sélectionne une fenêtre
    focalisée sur les termes de la question. Fallback tête du contenu.
    """
    caps = d.get("@search.captions") or []
    cap_text = caps[0].get("text") if caps else ""
    content_text = d.get("content") or ""
    base = (cap_text + "\n" + content_text).strip()

    terms = _extract_query_terms(question)
    if terms:
        return _best_window(base, terms, window=1400, step=350)

    # fallback si aucune clef dans la question
    return (cap_text or content_text)[:1200].strip()


# ============================================================
# Extraction d’un titre / chemin depuis metadata
# ============================================================
def _sanitize(s: Optional[str]) -> str:
    if not s:
        return ""
    return str(s).replace("\x00", "").strip().rstrip("\r\n")

def _extract_title(d: Dict[str, Any]) -> Optional[str]:
    """
    Nouvel index: utiliser file_name comme titre.
    """
    t = d.get("file_name")
    if t:
        return _sanitize(t)
    # Secours: tronquer content si besoin
    cnt = d.get("content") or d.get("table_markdown") or ""
    if cnt:
        head = cnt.strip().splitlines()[0][:80]
        return _sanitize(head) if head else None
    return None

def _extract_path(d: Dict[str, Any]) -> Optional[str]:
    """
    Nouvel index: pas de chemin persisté. On retourne None.
    Si tu veux un pseudo-path, dé-commente la ligne 'blob://'.
    """
    fn = d.get("file_name")
    if fn:
         return f"blob://{fn}"
    return None

# ============================================================
# Construction d’un document utilisé
# ============================================================

def _make_used_doc_from_context(c: Dict[str, Any]) -> Dict[str, Any]:
    meta = c.get("meta", {}) or {}
    title = _sanitize(c.get("title") or "Document")
    return {
        "id": meta.get("id"),
        "title": title,
        "path": meta.get("path"),     
        "score": meta.get("score"),
        "reranker": meta.get("reranker"),
    }
# ============================================================
# Vérifie si le document est dans le scope de confiance
# ============================================================


def _is_in_scope(hits: List[Dict[str, Any]]) -> bool:
    if not hits:
        return False
    top = hits[0]
    rer = top.get("@search.rerankerScore")
    if isinstance(rer, (int, float)):
        return rer >= RERANKER_MIN
    scr = top.get("@search.score")
    if isinstance(scr, (int, float)):
        return scr >= BM25_MIN
    return False


# ============================================================
# Nettoyage markdown basique
# ============================================================

def clean_plaintext(text: str) -> str:
    """Nettoyage minimal de markdown pour affichage RAG."""
    if not text:
        return ""
    t = text
    t = _MD_BOLD_RE.sub(r"\1", t)
    t = _MD_ITALIC_RE.sub(r"\1", t)
    t = _MD_HEADERS_RE.sub(r"\1", t)
    t = re.sub(r"`([^`]+)`", r"\1", t)
    return t.strip()

def _to_float_str_fr(x: Optional[str]) -> Optional[str]:
    if not x:
        return None
    s = str(x).replace(" ", "").replace(".", "")
    return s.replace(",", ".")

def _odata_escape(value: Optional[str]) -> str:
    if value is None:
        return ""
    return str(value).replace("'", "''")