import requests
from typing import Any, Dict, Optional

from app.core.config import (
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_API_KEY,
    VET_INDEX_NAME,
    VET_RETRIEVAL_K,
)

def _search_vet_docs(
    query: str,
    filters: Optional[Dict[str, Any]] = None,
    k: int = VET_RETRIEVAL_K,
) -> Dict[str, Any]:
    """
    Search spécifique sur l'index vétérinaire (VET_INDEX_NAME).
    """
    if not query:
        query = "*"

    url = f"{AZURE_SEARCH_ENDPOINT}/indexes/{VET_INDEX_NAME}/docs/search?api-version=2024-07-01"

    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_SEARCH_API_KEY,
    }

    body: Dict[str, Any] = {
        "search": query or "*",
        "queryType": "simple",
        "top": max(1, min(int(k or 10), 1000)),
    }

    # Filtres simples type {"category": "procedures"}
    if filters:
        filter_clauses = []
        for field, value in filters.items():
            if value is None or value == "":
                continue
            v = str(value).replace("'", "''")
            filter_clauses.append(f"{field} eq '{v}'")
        if filter_clauses:
            body["filter"] = " and ".join(filter_clauses)

    resp = requests.post(url, json=body, headers=headers, timeout=20)
    resp.raise_for_status()
    return resp.json()
