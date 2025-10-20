from __future__ import annotations

from typing import Any, Dict, Iterable, List


def _esc(v: Any) -> str:
    """Echappe les apostrophes pour OData."""
    return str(v).replace("'", "''")


def _in_list(values: Iterable[str]) -> str:
    # search.in(field,'a,b,c','|') n'est pas disponible ici: on compose via OR.
    vals = [f"'{_esc(v)}'" for v in values if str(v)]
    return ", ".join(vals)


def build_odata(filters: Dict[str, Any] | None) -> str:
    """
    Construit un filtre OData basique à partir d'un dict.
    Clés gérées par convention:
      - path_prefix: startswith(path, '...')
      - tenant_id:   tenant_id eq '...'
      - eq: dict de champs à tester en égalité stricte
      - any_in: dict { field: [v1, v2] } → (field eq 'v1' or field eq 'v2')
    """
    if not filters:
        return ""

    parts: List[str] = []

    # Spécifiques
    if "path_prefix" in filters and filters["path_prefix"]:
        parts.append(f"startswith(path, '{_esc(filters['path_prefix'])}')")

    if "tenant_id" in filters and filters["tenant_id"]:
        parts.append(f"tenant_id eq '{_esc(filters['tenant_id'])}'")

    # Egalités génériques
    eq = filters.get("eq") or {}
    if isinstance(eq, dict):
        for field, value in eq.items():
            if value is None or value == "":
                continue
            parts.append(f"{field} eq '{_esc(value)}'")

    # IN / OR list
    any_in = filters.get("any_in") or {}
    if isinstance(any_in, dict):
        for field, values in any_in.items():
            values = [v for v in (values or []) if str(v)]
            if not values:
                continue
            ors = [f"{field} eq '{_esc(v)}'" for v in values]
            parts.append("(" + " or ".join(ors) + ")")

    return " and ".join(parts)
