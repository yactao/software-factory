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

    select_fields_simple = (
        "id,entity_type,source_container,file_name,content,"
        "magasin_name,magasin_code,pdf_blob_url,image_blob_container,image_blob_urls,"
        "cv_person_name,cv_specialty,cv_emails,cv_phones,cv_blob_url,"
        "itemId,name,siteId,siteUrl,driveId,webUrl,path,lastModified,indexedAt,"
        "extracted_at,allowed_users,@search.score"
    )

    payload_simple: Dict[str, Any] = {
        "search": question,
        "queryType": "simple",
        "top": max(1, min(k, 1000)),
        "answers": "none",
        "select": select_fields_simple,
    }

    # =========================
    # BUILD FILTER (ORIGINAL)
    # =========================
    odata_filter = _build_odata_filter(filters)

    # entity_type filter
    entity_type = filters.get("entity_type") if isinstance(filters, dict) else None
    if entity_type:
        et_filter = f"entity_type eq '{entity_type}'"
        odata_filter = f"({odata_filter}) and {et_filter}" if odata_filter else et_filter

    # =========================
    # 🧠 DOCUMENT GROUNDING (NEW)
    # =========================
    doc_scope = filters.get("doc_scope") if isinstance(filters, dict) else None

    if isinstance(doc_scope, dict):
        scope_type = doc_scope.get("type")
        scope_value = doc_scope.get("value")

        if scope_value:
            scope_value = _odata_escape(str(scope_value))

            if scope_type == "sharepoint":
                scope_filter = f"itemId eq '{scope_value}'"

            elif scope_type == "audit":
                scope_filter = f"file_name eq '{scope_value}'"

            elif scope_type == "cv":
                scope_filter = f"cv_blob_url eq '{scope_value}'"

            else:
                scope_filter = None

            if scope_filter:
                odata_filter = f"({odata_filter}) and {scope_filter}" if odata_filter else scope_filter

    # apply filter
    if odata_filter:
        payload_simple["filter"] = odata_filter

    # =========================
    # EXECUTE SEARCH
    # =========================
    try:
        resp = requests.post(url, headers=headers, json=payload_simple, timeout=20)
    except RequestException as e:
        raise HTTPException(502, f"Search unreachable: {e}")

    if resp.status_code < 300:
        return resp.json()

    txt = resp.text or ""

    # retry without select if needed
    if ("Could not find a property named" in txt) or ("Parameter name: $select" in txt):
        payload_simple.pop("select", None)
        resp2 = requests.post(url, headers=headers, json=payload_simple, timeout=20)
        if resp2.status_code < 300:
            return resp2.json()
        resp = resp2

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
    """
    Recherche dans l'index 'mdm-finance-index' (magasin/dept/code_magasin/...).
    Paramètres:
      - q: texte libre (cherche sur les champs 'magasin', 'client_name', 'source_workbook')
      - ville: pour compat rétro, sert à filtrer soit dept (si numérique), soit magasin (si texte)
      - client: mappe vers client_name
    """
    _require_search_config()
    url = f"{AZURE_SEARCH_ENDPOINT}/indexes/{AZURE_SEARCH_INDEX_FINANCE}/docs/search?api-version={AZURE_SEARCH_API_VER}"
    headers = {"Content-Type": "application/json", "api-key": AZURE_SEARCH_API_KEY}

    def _is_numlike(s: str) -> bool:
        try:
            return str(s).strip() != "" and str(s).strip().replace(" ", "").isdigit()
        except Exception:
            return False

    filters: List[str] = []
    if ville:
        v = _odata_escape(ville.strip())
        if _is_numlike(v):
            # Interprète "ville" numérique comme un code de département (dept)
            filters.append(f"dept eq '{v}'")
        else:
            # Texte → filtre sur le nom du magasin (exact ou préfixe)
            filters.append(f"(magasin eq '{v}' or startswith(magasin, '{v}'))")
    if client:
        c = _odata_escape(client.strip())
        filters.append(f"client_name eq '{c}'")

    odata_filter = " and ".join(filters) if filters else None

    select_fields = (
        "id,magasin,dept,code_magasin,ve_an,gv,pv,montant_annuel,"
        "client_name,period_start,period_end,total_gv,total_pv,total_montant_annuel,"
        "source_workbook,sheet_name,sheet_index,updated_at"
    )

    payload: Dict[str, Any] = {
        # Recherche simple: si 'q' vide → wildcard
        "search": (q or "*"),
        "queryType": "simple",
        "top": min(max(int(top or 20), 1), 200),
        "select": select_fields,
    }
    if odata_filter:
        payload["filter"] = odata_filter

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=12)
    except RequestException as e:
        raise HTTPException(502, f"Azure Search injoignable: {e}")

    if r.status_code >= 300:
        raise HTTPException(r.status_code, f"Search error (finance/mdm): {r.text}")

    return r.json().get("value", [])
