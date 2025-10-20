"""
Configuration de logging unifiée (console, JSON optionnel) + helpers.

- `configure_root_logger()` : configure root logger selon variables d’env.
- `get_logger(name)` : récupère un logger prêt à l’emploi.
- `log_exceptions` : décorateur pour tracer exceptions et latence.
"""

from __future__ import annotations
import json
import logging
import os
import time
from typing import Callable, TypeVar, Any, cast

T = TypeVar("T")

_DEFAULT_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
_JSON = os.getenv("LOG_JSON", "false").lower() in ("1", "true", "yes", "on")


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "name": record.name,
            "msg": record.getMessage(),
        }
        # champs additionnels si présents
        for k in ("pathname", "lineno", "funcName"):
            payload[k] = getattr(record, k, None)
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_root_logger(level: str | int = _DEFAULT_LEVEL, json_mode: bool = _JSON) -> None:
    """Configure le root logger une seule fois."""
    root = logging.getLogger()
    if root.handlers:
        return  # déjà configuré

    root.setLevel(level if isinstance(level, int) else getattr(logging, str(level).upper(), logging.INFO))

    handler = logging.StreamHandler()
    if json_mode:
        handler.setFormatter(_JsonFormatter())
    else:
        fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        handler.setFormatter(logging.Formatter(fmt))
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Retourne un logger nommé, en s’assurant que le root est configuré."""
    configure_root_logger()
    return logging.getLogger(name)


def log_exceptions(fn: Callable[..., T]) -> Callable[..., T]:
    """
    Décorateur: log l’appel, la latence et capture l’exception en ERROR
    avec re-raise, pour garder le comportement originel.
    """
    log = get_logger(fn.__module__ + "." + fn.__name__)

    def wrapper(*args: Any, **kwargs: Any):  # type: ignore[override]
        t0 = time.time()
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            log.exception("Unhandled exception: %s", e)
            raise
        finally:
            dt = (time.time() - t0) * 1000
            log.debug("Elapsed %.1f ms", dt)

    return cast(Callable[..., T], wrapper)
