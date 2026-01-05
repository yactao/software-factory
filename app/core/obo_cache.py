# app/core/obo_cache.py
import time
from dataclasses import dataclass
from typing import Optional

@dataclass
class TokenEntry:
    token: str
    expires_at: float  # epoch seconds

class InMemoryTokenCache:
    def __init__(self) -> None:
        self._store: dict[str, TokenEntry] = {}

    def get(self, key: str) -> Optional[str]:
        entry = self._store.get(key)
        if not entry:
            return None
        if entry.expires_at <= time.time():
            self._store.pop(key, None)
            return None
        return entry.token

    def set(self, key: str, token: str, expires_in: int) -> None:
        # marge de sécurité 60s
        ttl = max(30, int(expires_in) - 60)
        self._store[key] = TokenEntry(token=token, expires_at=time.time() + ttl)

obo_cache = InMemoryTokenCache()
