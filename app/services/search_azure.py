import os
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
    """
    Recherche robuste pour index SANS semantic configuration.
    Stratégie:
      1) Envoie d'abord en mode 'simple' (BM25) sans 'semanticConfiguration' ni 'captions'.
      2) Si tu veux tester plus tard le mode sémantique, mets RAG_ALLOW_SEMANTIC=1
         ET assure-toi d'avoir une semantic configuration 'default' sur l'index.
         Dans ce cas seulement, on fera un 2e essai en 'semantic'.
    """
    _require_search_config()
    url = f"{AZURE_SEARCH_ENDPOINT}/indexes/{AZURE_SEARCH_INDEX}/docs/search?api-version={AZURE_SEARCH_API_VER}"
    headers = {"Content-Type": "application/json", "api-key": AZURE_SEARCH_API_KEY}

    # IMPORTANT: pas de @search.captions dans $select quand on est en simple
    # (sinon Azure peut râler sur des champs spéciaux non supportés)
    select_fields_simple = (
        "id,entity_type,source_container,file_name,content,"
        "magasin_name,magasin_code,pdf_blob_url,image_blob_container,image_blob_urls,"
        "cv_person_name,cv_specialty,cv_emails,cv_phones,cv_blob_url,extracted_at,"
        "@search.score"
    )


    # --------------- Requête 1: SIMPLE (toujours) ---------------
    payload_simple: Dict[str, Any] = {
        "search": question,
        "queryType": "simple",
        "top": max(1, min(k, 1000)),
        "answers": "none",
        "select": select_fields_simple,
    }
    odata_filter = _build_odata_filter(filters)
    if odata_filter:
        payload_simple["filter"] = odata_filter

    try:
        resp = requests.post(url, headers=headers, json=payload_simple, timeout=20)
    except RequestException as e:
        raise HTTPException(502, f"Search unreachable: {e}")
    # Si ça passe en simple, on retourne tout de suite
    if resp.status_code < 300:
        return resp.json()

    # Si l’échec vient d’un $select invalide, on retire $select et on retente en simple
    txt = resp.text or ""
    if ("Could not find a property named" in txt) or ("Parameter name: $select" in txt):
        payload_simple.pop("select", None)
        resp2 = requests.post(url, headers=headers, json=payload_simple, timeout=20)
        if resp2.status_code < 300:
            return resp2.json()
        # Si ça échoue encore, on continue le flux ci-dessous avec resp2
        resp = resp2
        txt = resp.text or ""

    # --------------- Optionnel: Requête 2 SEMANTIC (seulement si autorisé + index prêt) ---------------
    # Active ce test UNIQUEMENT si tu as créé une semantic configuration 'default'
    # et que tu as mis RAG_ALLOW_SEMANTIC=1 dans l'env.
    try_semantic = os.getenv("RAG_ALLOW_SEMANTIC", "0") == "1"
    if try_semantic:
        payload_sem: Dict[str, Any] = {
            "search": question,
            "queryType": "semantic",
            "semanticConfiguration": os.getenv("RAG_SEM_CONFIG", "default"),
            "top": max(1, min(k, 1000)),
            "answers": "none",
            "captions": "extractive",
            "select": (
                "id,doc_id,file_name,chunk_type,section_path,page,"
                "content,content_raw,table_markdown,checkbox_lines,"
                "token_count,chunk_index,chunk_count,hash,"
                "@search.score,@search.rerankerScore,@search.captions"
            ),
        }
        if odata_filter:
            payload_sem["filter"] = odata_filter

        resp_sem = requests.post(url, headers=headers, json=payload_sem, timeout=20)
        if resp_sem.status_code < 300:
            return resp_sem.json()

        sem_txt = resp_sem.text or ""
        # Si l’index N’A PAS de semantic config, on NE ré-essaie pas en semantic
        if ("semanticconfiguration" in sem_txt.lower()) or ("querytype" in sem_txt.lower() and "semantic" in sem_txt.lower()):
            # On retombe explicitement en simple (déjà tenté ci-dessus),
            # donc on renverra l’erreur simple ci-dessous.
            pass
        else:
            # On tente un repli $select en semantic (au cas où certains champs manquent)
            if ("Could not find a property named" in sem_txt) or ("Parameter name: $select" in sem_txt):
                payload_sem.pop("select", None)
                resp_sem2 = requests.post(url, headers=headers, json=payload_sem, timeout=20)
                if resp_sem2.status_code < 300:
                    return resp_sem2.json()
            # Si on arrive ici, l’essai semantic a échoué pour une autre raison;
            # on laissera tomber sur l’erreur simple plus bas.

    # --------------- Si on est ici: tout a échoué ---------------
    raise HTTPException(resp.status_code, f"Search error: {resp.text}")

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

    # L’index ne contient pas de champs 'Ville' / 'Client'. On les injecte dans le texte de recherche.
    search_text = " ".join([s for s in [q or "", ville or "", client or ""] if s.strip()]) or "*"

    payload: Dict[str, Any] = {
        "search": search_text,
        "queryType": "simple",
        "top": min(max(int(top or 20), 1), 50),
        "select": (
            "id,entity_type,file_name,sheet_index,sheet_name,row_count,column_count,content,"
            "csv_blob_container,csv_blob_name,csv_blob_url,extracted_at,schema,numeric_summary"
        ),
    }

    r = requests.post(url, headers=headers, json=payload, timeout=10)
    if r.status_code >= 300:
        txt = r.text or ""
        # Repli doux si $select tombe sur un champ non reconnu
        if "Could not find a property named" in txt or "Parameter name: $select" in txt:
            payload.pop("select", None)
            r2 = requests.post(url, headers=headers, json=payload, timeout=10)
            if r2.status_code >= 300:
                raise HTTPException(r2.status_code, f"Search error (finance): {r2.text}")
            return r2.json().get("value", [])
        raise HTTPException(r.status_code, f"Search error (finance): {txt}")

    return r.json().get("value", [])
