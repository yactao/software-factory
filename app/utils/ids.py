"""
Génération d'identifiants stables et sûrs pour conversations et clés Table Storage.
"""

from __future__ import annotations
import re
import random
import datetime as _dt
from typing import Dict, Any

# Caractères interdits par Azure Table Storage pour PartitionKey/RowKey
INVALID_KEY_CHARS_RE = re.compile(r"[#?/\\\x00-\x1F]")

def safe_key(value: str | None, max_len: int = 900) -> str:
    """
    Nettoie une clé pour Azure Table Storage.
    - remplace les caractères interdits par '_'
    - coupe à max_len caractères
    """
    if not value:
        return ""
    s = INVALID_KEY_CHARS_RE.sub("_", str(value))
    return s[:max_len]


def short_id(n: int = 6) -> str:
    """Petit identifiant alphanumérique pour suffixes."""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(random.choice(alphabet) for _ in range(max(2, n)))


def new_conversation_id(prefix: str = "conv") -> str:
    """
    ID conversation horodaté: conv-YYYYMMDD-HHMMSS-RAND
    """
    ts = _dt.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    return f"{prefix}-{ts}-{random.randint(1000, 9999)}"


def new_rowkey() -> str:
    """
    RowKey triable chronologiquement: YYYYMMDDHHMMSSffffff-RAND
    Idéal pour conserver l’ordre dans Table Storage.
    """
    return _dt.datetime.utcnow().strftime("%Y%m%d%H%M%S%f") + f"-{random.randint(1000, 9999)}"


def pk_from_claims(claims: Dict[str, Any]) -> str:
    """
    Construit la PartitionKey à partir des claims AAD:
    - tid: tenant id
    - sub (ou oid): subject id
    """
    tid = str(claims.get("tid") or "").strip()
    sub = str(claims.get("sub") or claims.get("oid") or "").strip()
    return safe_key(f"{tid}|{sub}")
