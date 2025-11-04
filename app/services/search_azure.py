import requests
from typing import Dict, Any, Optional, List
from app.utils.snippets import _odata_escape
from fastapi import HTTPException
from requests.exceptions import RequestException
from ..core.config import (
    AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_API_VER, AZURE_SEARCH_API_KEY,
    AZURE_SEARCH_INDEX, AZURE_SEARCH_INDEX_TRADING, AZURE_SEARCH_INDEX_FINANCE,
    RAG_USE_VECTOR, RAG_VECTOR_INTEGRATED, RAG_VECTOR_FIELDS, RAG_VECTOR_K,
    RETRIEVAL_K, RAG_SEM_CONFIG
)
from ..utils.filters import _build_odata_filter, _build_odata_filter_trading
from ..utils.embeddings import _embed_text_aoai


def _require_search_config():
    if not AZURE_SEARCH_ENDPOINT or not AZURE_SEARCH_API_KEY:
        raise HTTPException(500, "Search endpoint ou clé non configurés. Vérifie AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_API_KEY, AZURE_SEARCH_INDEX, AZURE_SEARCH_API_VERSION.")


def _search_docs(question: str, filters: Optional[Dict[str, Any]], k: int = RETRIEVAL_K) -> Dict[str, Any]:
    _require_search_config()
    url = f"{AZURE_SEARCH_ENDPOINT}/indexes/{AZURE_SEARCH_INDEX}/docs/search?api-version={AZURE_SEARCH_API_VER}"
    headers = {"Content-Type": "application/json", "api-key": AZURE_SEARCH_API_KEY}

    select_fields = (
        "id,doc_id,file_name,chunk_type,section_path,page,"
        "content,content_raw,table_markdown,checkbox_lines,"
        "token_count,chunk_index,chunk_count,hash,"
        "@search.rerankerScore,@search.score,@search.captions"
    )

    payload: Dict[str, Any] = {
        "search": question,
        "queryType": "semantic",
        "semanticConfiguration": RAG_SEM_CONFIG,   # "sem-default"
        "top": max(1, min(k, 1000)),
        "captions": "extractive",
        "answers": "extractive|count-3",
        "select": select_fields,
    }

    # Filtre OData (adapté au nouveau schéma)
    odata_filter = _build_odata_filter(filters)
    if odata_filter:
        payload["filter"] = odata_filter

    # ----- Partie vectorielle -----
    try_vector = RAG_USE_VECTOR
    if try_vector:
        if RAG_VECTOR_INTEGRATED:
            # Nécessite API Search >= 2024-05-01 ; va casser en 2023-11-01 (ton cas actuel)
            payload["vectorQueries"] = [{
                "vectorizer": "vz-aoai",
                "fields": RAG_VECTOR_FIELDS,                 # "content_vector"
                "text": question,
                "kNearestNeighbors": max(1, min(RAG_VECTOR_K, 1000))
            }]
        else:
            # Mode classique 2023-11-01 : on fournit le vecteur directement
            vec = _embed_text_aoai(question)
            if vec:
                payload["vectorQueries"] = [{
                    "vector": vec,
                    "fields": RAG_VECTOR_FIELDS,             # "content_vector"
                    "kNearestNeighbors": max(1, min(RAG_VECTOR_K, 1000))
                }]
            else:
                # Pas d'embedding dispo → on reste en BM25 + semantic uniquement
                pass

    # ----- Appel Search avec repli progressif -----
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
    except RequestException as e:
        raise HTTPException(502, f"Search unreachable: {e}")

    if resp.status_code >= 300:
        txt = resp.text or ""

        # Si l'erreur vient de 'vectorizer' (API trop ancienne), on retente en mode classique avec embedding
        if "vectorizer" in txt and not RAG_VECTOR_INTEGRATED:
            # rien à faire: on n'utilise déjà pas 'vectorizer'
            pass
        elif "vectorizer" in txt and RAG_VECTOR_INTEGRATED:
            # Retirer le 'vectorizer' et basculer en vecteur brut
            try:
                vec = _embed_text_aoai(question)
                if vec:
                    payload["vectorQueries"] = [{
                        "vector": vec,
                        "fields": RAG_VECTOR_FIELDS,
                        "kNearestNeighbors": max(1, min(RAG_VECTOR_K, 1000))
                    }]
                else:
                    payload.pop("vectorQueries", None)
                resp = requests.post(url, headers=headers, json=payload, timeout=20)
            except Exception:
                # si tout échoue, on tentera les replis ci-dessous
                pass

        # Replis standard si champ absent dans $select
        if resp.status_code >= 300:
            txt = resp.text or ""
            if "Could not find a property named" in txt or "Parameter name: $select" in txt:
                payload.pop("select", None)
                resp = requests.post(url, headers=headers, json=payload, timeout=20)

        # Answers non supportés
        if resp.status_code >= 300 and "answer" in (txt.lower()):
            payload["answers"] = "none"
            resp = requests.post(url, headers=headers, json=payload, timeout=20)

        # Semantic config absente → simple
        if resp.status_code >= 300 and ("semantic" in txt.lower()):
            payload["queryType"] = "simple"
            payload.pop("semanticConfiguration", None)
            resp = requests.post(url, headers=headers, json=payload, timeout=20)

        # Dernier essai: retirer complètement vectorQueries si toujours en erreur
        if resp.status_code >= 300 and "vector" in (txt.lower()):
            payload.pop("vectorQueries", None)
            resp = requests.post(url, headers=headers, json=payload, timeout=20)

        if resp.status_code >= 300:
            raise HTTPException(resp.status_code, f"Search error: {resp.text}")

    return resp.json()

def _search_trading_docs(question: str, filters: Optional[Dict[str, Any]], k: int = RETRIEVAL_K) -> Dict[str, Any]:
    _require_search_config()
    if not AZURE_SEARCH_INDEX_TRADING:
        raise HTTPException(500, "AZURE_SEARCH_INDEX_TRADING non défini.")
    url = f"{AZURE_SEARCH_ENDPOINT}/indexes/{AZURE_SEARCH_INDEX_TRADING}/docs/search?api-version={AZURE_SEARCH_API_VER}"
    headers = {"Content-Type": "application/json", "api-key": AZURE_SEARCH_API_KEY}

    payload: Dict[str, Any] = {
        "search": question,
        "queryType": "semantic",
        "semanticConfiguration": "default",
        "top": k,
        "select": (
            "id,title,content,source_path,tenant_id,chunk_index,"
            "commodity,product_type,region,route,port,operation_type,"
            "vessel_class,contract_type,hedge_instruments,jurisdiction,"
            "metadata_storage_path,metadata_storage_name,metadata_title,"
            "file_name,filename,@search.rerankerScore"
        ),
        "captions": "extractive",            
        "answers": "none"
    }

    odata_filter = _build_odata_filter_trading(filters)
    if odata_filter:
        payload["filter"] = odata_filter

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
    except RequestException as e:
        raise HTTPException(502, f"Search unreachable: {e}")

    if resp.status_code >= 300:
        # Repli si $select pose souci
        txt = resp.text or ""
        if "Could not find a property named" in txt or "Parameter name: $select" in txt:
            payload.pop("select", None)
            resp2 = requests.post(url, headers=headers, json=payload, timeout=15)
            if resp2.status_code >= 300:
                raise HTTPException(resp2.status_code, f"Search error: {resp2.text}")
            return resp2.json()
        raise HTTPException(resp.status_code, f"Search error: {resp.text}")
    return resp.json()

def _search_finance(q: str, ville: Optional[str], client: Optional[str], top: int = 20) -> List[Dict[str, Any]]:
    _require_search_config()
    url = f"{AZURE_SEARCH_ENDPOINT}/indexes/{AZURE_SEARCH_INDEX_FINANCE}/docs/search?api-version={AZURE_SEARCH_API_VER}"
    headers = {"Content-Type": "application/json", "api-key": AZURE_SEARCH_API_KEY}

    filters = []
    if ville:
        v = _odata_escape(ville)
        filters.append(f"Ville eq '{v}'")
    if client:
        c = _odata_escape(client)
        filters.append(f"Client eq '{c}'")
    odata_filter = " and ".join(filters) if filters else None

    payload: Dict[str, Any] = {
        "search": q if q else "*",
        "queryType": "simple",
        "top": min(max(int(top or 20), 1), 200),
        "select": "row_id,Date,N_Piece,Client,Ville,Nature,Compte,Montant_HT,TVA_20,Montant_TTC,Compte_Tiers",
    }
    if odata_filter:
        payload["filter"] = odata_filter

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
    except RequestException as e:
        raise HTTPException(502, f"Azure Search injoignable: {e}")

    if r.status_code >= 300:
        raise HTTPException(r.status_code, f"Search error (finance): {r.text}")
    return r.json().get("value", [])
