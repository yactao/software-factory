# app/services/search_azure_trading_doc.py
"""
Azure AI Search service for the trading documents index (aina-trading-docs-idx).
Semantic search only; used by POST /api/trading/doc.
"""

import os
from typing import Dict, Any, Optional, List

import requests
from requests.exceptions import RequestException
from fastapi import HTTPException

from app.core.config import (
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_API_VER,
    AZURE_SEARCH_API_KEY,
)

# Index name: env or fallback
AZURE_SEARCH_INDEX_TRADING_DOC = os.getenv(
    "AZURE_SEARCH_INDEX_TRADING_DOC",
    "aina-trading-docs-idx",
)

SEMANTIC_CONFIG = "semantic-config"
SELECT_FIELDS = (
    "chunk_id,doc_id,topic_id,language,title,display_name,section,"
    "chunk_index,content,blob_name,"
    "@search.score,@search.rerankerScore,@search.captions"
)
SEARCH_TIMEOUT = 20


def _require_search_config() -> None:
    if not AZURE_SEARCH_ENDPOINT or not AZURE_SEARCH_API_KEY:
        raise HTTPException(
            500,
            "Search endpoint or key not configured. Check AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_API_KEY.",
        )
    if not AZURE_SEARCH_INDEX_TRADING_DOC:
        raise HTTPException(500, "AZURE_SEARCH_INDEX_TRADING_DOC not set.")


def _odata_escape(value: Optional[str]) -> str:
    if value is None:
        return ""
    return str(value).replace("'", "''")


def _build_trading_doc_filter(
    language: str,
    filters: Optional[Dict[str, Any]],
) -> Optional[str]:
    """
    Build OData filter:
      - language eq 'fr' or 'en'
      - if filters.topic_id -> topic_id eq '...'
      - if filters.doc_id -> doc_id eq '...'
      - if filters.display_name -> display_name eq '...'
    """
    clauses: List[str] = []
    lang = (language or "fr").strip().lower()
    if lang not in ("fr", "en"):
        lang = "fr"
    clauses.append(f"language eq '{lang}'")

    if filters:
        if filters.get("topic_id") is not None:
            clauses.append(f"topic_id eq '{_odata_escape(str(filters['topic_id']))}'")
        if filters.get("doc_id") is not None:
            clauses.append(f"doc_id eq '{_odata_escape(str(filters['doc_id']))}'")
        if filters.get("display_name") is not None:
            clauses.append(
                f"display_name eq '{_odata_escape(str(filters['display_name']))}'"
            )

    return " and ".join(clauses) if clauses else None


def search_trading_doc_chunks(
    question: str,
    filters: Optional[Dict[str, Any]],
    k: int,
    language: str = "fr",
) -> Dict[str, Any]:
    """
    Query Azure AI Search index for trading docs with semantic search.

    Args:
        question: search query
        filters: optional dict with topic_id, doc_id, display_name
        k: top-k results
        language: 'fr' or 'en' (used in OData filter)

    Returns:
        Raw Azure Search response (value, @search.captions, etc.)
    """
    _require_search_config()
    url = (
        f"{AZURE_SEARCH_ENDPOINT}/indexes/{AZURE_SEARCH_INDEX_TRADING_DOC}"
        f"/docs/search?api-version={AZURE_SEARCH_API_VER}"
    )
    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_SEARCH_API_KEY,
    }

    odata_filter = _build_trading_doc_filter(language, filters)
    top = max(1, min(k, 100))

    payload: Dict[str, Any] = {
        "search": question,
        "queryType": "semantic",
        "semanticConfiguration": SEMANTIC_CONFIG,
        "captions": "extractive",
        "answers": "none",
        "top": top,
        "select": SELECT_FIELDS,
    }
    if odata_filter:
        payload["filter"] = odata_filter

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=SEARCH_TIMEOUT)
    except RequestException as e:
        raise HTTPException(502, f"Search unreachable: {e}")

    if resp.status_code >= 300:
        txt = resp.text or ""
        if "Could not find a property named" in txt or "Parameter name: $select" in txt:
            payload.pop("select", None)
            resp2 = requests.post(
                url, headers=headers, json=payload, timeout=SEARCH_TIMEOUT
            )
            if resp2.status_code < 300:
                return resp2.json()
            raise HTTPException(resp2.status_code, f"Search error: {resp2.text}")
        raise HTTPException(resp.status_code, f"Search error: {resp.text}")

    return resp.json()
