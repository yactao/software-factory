import re

_MD_BOLD_RE = re.compile(r"\*\*(.*?)\*\*")
_MD_ITALIC_RE = re.compile(r"(?<!\*)\*(?!\*)(.*?)\*(?<!\*)")
_MD_HEADERS_RE = re.compile(r"^\s{0,3}#{1,6}\s*", re.MULTILINE)
_MD_BULLET_RE = re.compile(r"^\s*[-*]\s+", re.MULTILINE)
_MD_CODEBLOCK_RE = re.compile(r"```.*?```", re.DOTALL)
_MD_INLINE_CODE_RE = re.compile(r"`([^`]*)`")
_MD_NUM_BULLET_RE = re.compile(r"^\s*(?:\d+[\.)]|[a-zA-Z][\.)])\s+", re.MULTILINE)
_MD_DASH_BULLET_RE = re.compile(r"^\s*[-•●▪◦]\s+", re.MULTILINE)
_MD_UNDERLINE_TITLE_RE = re.compile(r"^\s*[_=]{3,}\s*$", re.MULTILINE)
_BRACKET_CITS_RE = re.compile(r"\[\s*\d+(?:\s*,\s*\d+)*\s*\]")

def _clean_model_text(s: str) -> str:
    if not s: return ""
    s = _MD_BOLD_RE.sub(r"\1", s)
    s = _MD_ITALIC_RE.sub(r"\1", s)
    s = _MD_HEADERS_RE.sub("", s)
    s = _MD_BULLET_RE.sub(" - ", s)
    s = re.sub(r"[ \t]+", " ", s).strip()
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s

def _clean_plaintext_no_bullets_titles(s: str) -> str:
    if not s: return ""
    s = _MD_CODEBLOCK_RE.sub("", s)
    s = _MD_INLINE_CODE_RE.sub(r"\1", s)
    s = _MD_BOLD_RE.sub(r"\1", s)
    s = _MD_ITALIC_RE.sub(r"\1", s)
    s = _MD_HEADERS_RE.sub("", s)
    s = _MD_UNDERLINE_TITLE_RE.sub("", s)
    s = _MD_DASH_BULLET_RE.sub("", s)
    s = _MD_NUM_BULLET_RE.sub("", s)
    s = s.replace("*", "")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def _clean_trading(s: str) -> str:
    if not s: return ""
    s = _BRACKET_CITS_RE.sub("", s)
    s = _MD_CODEBLOCK_RE.sub("", s)
    s = _MD_INLINE_CODE_RE.sub(r"\1", s)
    s = _MD_BOLD_RE.sub(r"\1", s)
    s = _MD_ITALIC_RE.sub(r"\1", s)
    s = _MD_HEADERS_RE.sub("", s)
    s = _MD_UNDERLINE_TITLE_RE.sub("", s)
    s = s.replace("*", "")
    s = re.sub(r"[ \t]+", " ", s).strip()
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s
