"""
Utilitaires communs (texte, ids, logging) pour l’orchestrateur RAG.

Expose des helpers fréquemment utilisés ailleurs dans l’app.
"""

from .text import (
    squeeze_spaces,
    normalize_newlines,
    strip_controls,
    clean_markdown,
    clean_plaintext_no_bullets_titles,
    clean_trading_text,
    remove_bracket_citations,
    clip,
    preview,
)

from .ids import (
    INVALID_KEY_CHARS_RE,
    safe_key,
    short_id,
    new_conversation_id,
    new_rowkey,
    pk_from_claims,
)

from .logging import (
    get_logger,
    configure_root_logger,
    log_exceptions,
)
