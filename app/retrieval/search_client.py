from __future__ import annotations

import json
from typing import Any, Dict, Optional

import requests
from fastapi import HTTPException

from app.settings import get_settings
from app.retrieval.filters import build_odata


class AzureSearch:
    """
    Client générique pour Azure AI Search:
    - construit la requête /docs/search
    - gère les options answers/captions/select
    - applique des fallbacks si l'API ou l'index ne supporte pas certaines features
    """

    def __init__(self):
        s = get_settings()
        self.endpoint: str = str(s.search_endpoint)
        self.key: str = s.search_api_key
        self.api_ver: str = s.search_api_version
        self._headers = {
            "Content-Type": "application/json",
            "api-key": self.key,
        }

    def _url(self, index: str) -> str:
        return f"{self.endpoint}/indexes/{index}/docs/search?api-version={self.api_ver}"

    def search(
        self,
        index: str,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top: int = 50,
        *,
        answers: bool = True,
        captions: bool = True,
        query_type: str = "semantic",               # "semantic" ou "simple"
        semantic_config: Optional[str] = "semantic-config",
        select: Optional[str] = (
            "id,title,content,path,source_path,metadata_title,"
            "@search.rerankerScore,@search.score,@search.captions"
        ),
        timeout: int = 15,
    ) -> Dict[str, Any]:
        """
        Exécute une recherche et renvoie la réponse JSON.
        Fallbacks automatiques:
          1) retire $select si un champ inconnu déclenche une erreur
          2) coupe answers si non supporté
          3) bascule en queryType="simple" si la semantic config n'existe pas
        """
        if not query:
            query = "*"

        body: Dict[str, Any] = {
            "search": query,
            "top": max(1, min(int(top or 1), 200)),
            "queryType": query_type,
        }

        if captions:
            body["captions"] = "extractive"
        if answers:
            body["answers"] = "extractive|count-3"
        if select:
            body["select"] = select
        if semantic_config and query_type == "semantic":
            body["semanticConfiguration"] = semantic_config

        odata = build_odata(filters)
        if odata:
            body["filter"] = odata

        url = self._url(index)

        def _post(payload: Dict[str, Any]) -> requests.Response:
            try:
                return requests.post(url, headers=self._headers, json=payload, timeout=timeout)
            except requests.RequestException as e:
                raise HTTPException(502, f"Azure Search injoignable: {e}")

        # 1er essai
        r = _post(body)
        if r.status_code < 300:
            return r.json()

        txt = r.text or ""

        # Fallback 1: retirer select si un champ est inconnu
        if "Could not find a property named" in txt or "Parameter name: $select" in txt:
            body.pop("select", None)
            r = _post(body)
            if r.status_code < 300:
                return r.json()
            txt = r.text or ""

        # Fallback 2: désactiver answers si non supporté (SKU/preview)
        if "answers" in txt.lower():
            body.pop("answers", None)
            r = _post(body)
            if r.status_code < 300:
                return r.json()
            txt = r.text or ""

        # Fallback 3: basculer en simple query si semantic_config manquante
        if "semantic" in txt.lower():
            body["queryType"] = "simple"
            body.pop("semanticConfiguration", None)
            r = _post(body)
            if r.status_code < 300:
                return r.json()

        # Echec final
        raise HTTPException(r.status_code, f"Search error: {r.text}")
