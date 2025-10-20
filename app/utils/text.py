"""
Nettoyage et normalisation de texte pour les sorties LLM et la mise en contexte.

Ce module fournit:
- Nettoyage Markdown → texte brut (sans puces, sans titres).
- Variante stricte pour Trading (supprime les références [n]).
- Helpers pour réduire le bruit (espaces, sauts de ligne, caractères de contrôle).
"""

from __future__ import annotations
import re
from typing import Iterable

# ---- Expressions régulières réutilisées (compatibles avec le code des routes) ----

MD_CODEBLOCK_RE = re.compile(r"```.*?```", re.DOTALL)
MD_INLINE_CODE_RE = re.compile(r"`([^`]*)`")
MD_BOLD_RE = re.compile(r"\*\*(.*?)\*\*")
MD_ITALIC_RE = re.compile(r"(?<!\*)\*(?!\*)(.*?)\*(?<!\*)")
MD_HEADERS_RE = re.compile(r"^\s{0,3}#{1,6}\s*", re.MULTILINE)
MD_UNDERLINE_TITLE_RE = re.compile(r"^\s*[_=]{3,}\s*$", re.MULTILINE)
MD_DASH_BULLET_RE = re.compile(r"^\s*[-•●▪◦]\s+", re.MULTILINE)
MD_NUM_BULLET_RE = re.compile(r"^\s*(?:\d+[\.)]|[a-zA-Z][\.)])\s+", re.MULTILINE)

# Citations type [1] ou [1, 2, 5]
BRACKET_CITATIONS_RE = re.compile(r"\[\s*\d+(?:\s*,\s*\d+)*\s*\]")

# Caractères de contrôle ASCII (0x00–0x1F) hors tab \t, LF \n, CR \r
CTRL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")

MULTISPACES_RE = re.compile(r"[ \t]+")
MULTINEWLINES_RE = re.compile(r"\n{3,}")


# ---- Helpers génériques -------------------------------------------------------

def squeeze_spaces(s: str) -> str:
    """Compacte espaces et tabulations consécutifs en un espace simple."""
    return MULTISPACES_RE.sub(" ", s)


def normalize_newlines(s: str) -> str:
    """Réduit les sauts de ligne successifs et coupe les marges inutiles."""
    s = MULTINEWLINES_RE.sub("\n\n", s)
    return s.strip()


def strip_controls(s: str) -> str:
    """Supprime les caractères de contrôle non imprimables (hors tab/CR/LF)."""
    return CTRL_CHARS_RE.sub("", s)


def clip(s: str, max_chars: int, keep_tail: bool = False) -> str:
    """Tronque proprement la chaîne à `max_chars` caractères."""
    if max_chars <= 0 or len(s) <= max_chars:
        return s
    if keep_tail:
        return s[-max_chars:]
    return s[:max_chars]


def preview(s: str, head: int = 160) -> str:
    """Retourne un aperçu court, pratique pour les logs."""
    s = s.replace("\n", " ")
    return clip(s, head)


# ---- Nettoyages principaux ----------------------------------------------------

def _strip_markdown_common(s: str) -> str:
    """Retire les éléments Markdown courants (code, gras, italique, titres, soulignés)."""
    s = MD_CODEBLOCK_RE.sub("", s)
    s = MD_INLINE_CODE_RE.sub(r"\1", s)
    s = MD_BOLD_RE.sub(r"\1", s)
    s = MD_ITALIC_RE.sub(r"\1", s)
    s = MD_HEADERS_RE.sub("", s)
    s = MD_UNDERLINE_TITLE_RE.sub("", s)
    return s


def clean_markdown(s: str) -> str:
    """
    Nettoie un texte Markdown en texte brut, mais conserve les listes
    (ne supprime pas explicitement les puces). Idéal pour un rendu simple.
    """
    if not s:
        return ""
    s = strip_controls(s)
    s = _strip_markdown_common(s)
    s = squeeze_spaces(s)
    s = normalize_newlines(s)
    return s


def clean_plaintext_no_bullets_titles(s: str) -> str:
    """
    Nettoyage strict: pas de Markdown, pas de puces (tirets/points), pas de listes numérotées,
    pas de titres. Sortie texte brut propre pour les réponses "prompt-only".
    """
    if not s:
        return ""
    s = strip_controls(s)
    s = _strip_markdown_common(s)
    s = MD_DASH_BULLET_RE.sub("", s)
    s = MD_NUM_BULLET_RE.sub("", s)
    s = s.replace("*", "")
    s = squeeze_spaces(s)
    s = normalize_newlines(s)
    return s


def remove_bracket_citations(s: str) -> str:
    """Supprime les séquences de type [1] ou [1, 2, 5]."""
    if not s:
        return ""
    return BRACKET_CITATIONS_RE.sub("", s)


def clean_trading_text(s: str) -> str:
    """
    Nettoyage pour le domaine Trading:
    - supprime citations [n]
    - supprime artefacts Markdown
    - garde des paragraphes lisibles
    """
    if not s:
        return ""
    s = strip_controls(s)
    s = remove_bracket_citations(s)
    s = MD_CODEBLOCK_RE.sub("", s)
    s = MD_INLINE_CODE_RE.sub(r"\1", s)
    s = MD_BOLD_RE.sub(r"\1", s)
    s = MD_ITALIC_RE.sub(r"\1", s)
    s = MD_HEADERS_RE.sub("", s)
    s = MD_UNDERLINE_TITLE_RE.sub("", s)
    s = s.replace("*", "")
    s = squeeze_spaces(s)
    s = normalize_newlines(s)
    return s
