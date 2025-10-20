from __future__ import annotations

import json
from functools import lru_cache
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from azure.data.tables import TableServiceClient
from azure.core.pipeline.policies import RetryPolicy

from app.settings import get_settings
from app.utils.ids import new_rowkey, pk_from_claims, safe_key

_table_service_cached: Optional[TableServiceClient] = None

CHAT_TABLE_ENV = "AZURE_TABLE_CHAT"
DEFAULT_CHAT_TABLE = "chatmessages"


@lru_cache
def get_table_service() -> TableServiceClient:
    """
    Retourne un TableServiceClient en utilisant soit:
    - AZURE_STORAGE_CONNECTION_STRING, soit
    - AZURE_STORAGE_ACCOUNT + AZURE_STORAGE_ACCOUNT_KEY.
    """
    global _table_service_cached
    if _table_service_cached is not None:
        return _table_service_cached

    s = get_settings()

    retry = RetryPolicy(total_retries=2, retry_backoff_factor=0.5)

    if s.storage_conn:
        _table_service_cached = TableServiceClient.from_connection_string(
            s.storage_conn,
            retry_policy=retry,
            connection_timeout=5,
            read_timeout=5,
        )
        return _table_service_cached

    if s.storage_account and s.storage_key:
        conn = (
            "DefaultEndpointsProtocol=https;"
            f"AccountName={s.storage_account};"
            f"AccountKey={s.storage_key};"
            "EndpointSuffix=core.windows.net"
        )
        _table_service_cached = TableServiceClient.from_connection_string(
            conn,
            retry_policy=retry,
            connection_timeout=5,
            read_timeout=5,
        )
        return _table_service_cached

    # Rien de configuré → erreur claire
    raise RuntimeError(
        "Table Storage non configuré. "
        "Définis AZURE_STORAGE_CONNECTION_STRING ou AZURE_STORAGE_ACCOUNT + AZURE_STORAGE_ACCOUNT_KEY."
    )

def get_chat_table():
    svc = get_table_service()
    s = get_settings()
    table_name = s.azure_table_chat or "chatmessages"
    # Crée si pas présent, puis retourne le client
    try:
        svc.create_table_if_not_exists(table_name)
    except Exception:
        pass
    return svc.get_table_client(table_name)

def list_conversation_events(claims: dict, conversation_id: str):
    table = get_chat_table()
    tid = (claims.get("tid") or "").strip()
    sub = (claims.get("sub") or claims.get("oid") or "").strip()
    pk = f"{tid}|{sub}"

    items = list(table.query_entities(
        query_filter=f"PartitionKey eq '{pk}' and conversation_id eq '{conversation_id}'",
        select=["PartitionKey","RowKey","role","route","message","timestamp_utc","meta_json"]
    ))
    items.sort(key=lambda x: x.get("RowKey", ""))

    out = []
    for it in items:
        meta_raw = it.get("meta_json")
        meta = {}
        if meta_raw:
            try:
                import json
                meta = json.loads(meta_raw)
            except Exception:
                meta = {"_meta_json_error": True}
        out.append({
            "role": it.get("role"),
            "route": it.get("route"),
            "message": it.get("message") or "",
            "timestamp_utc": it.get("timestamp_utc"),
            "meta": meta,
        })
    return out
def _chat_table_name() -> str:
    import os
    return os.getenv(CHAT_TABLE_ENV, DEFAULT_CHAT_TABLE)




def _pack_meta(meta: Optional[Dict[str, Any]], limit_chars: int = 32000) -> str:
    """
    Sérialise meta en JSON, avec une troncature défensive si nécessaire.
    """
    if not meta:
        return "{}"
    try:
        s = json.dumps(meta, ensure_ascii=False)
        return s[:limit_chars]
    except Exception:
        return "{}"


def save_chat_event(
    claims: Dict[str, Any],
    conversation_id: Optional[str],
    role: str,
    route: str,
    message: str,
    meta: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Enregistre un évènement de chat (user/assistant/meta) et retourne conversation_id.
    - PartitionKey: <tenant>|<user> (depuis claims)
    - RowKey: triable chrono (new_rowkey)
    """
    if not claims:
        raise HTTPException(500, "Claims manquants pour l’historisation.")

    table = get_chat_table()
    conv = conversation_id or f"conv-{safe_key(route)}"

    entity = {
        "PartitionKey": pk_from_claims(claims),
        "RowKey": new_rowkey(),
        "conversation_id": conv,
        "role": role,
        "route": route,
        "message": (message or "")[:32000],
        "meta_json": _pack_meta(meta),
    }

    try:
        table.upsert_entity(entity)
    except Exception as e:
        raise HTTPException(500, f"Table Storage indisponible: {e}")

    return conv



def delete_conversation(claims: Dict[str, Any], conversation_id: str) -> int:
    """
    Supprime toutes les entrées d’une conversation. Retourne le nombre supprimé.
    """
    table = get_chat_table()
    pk = pk_from_claims(claims)
    try:
        to_delete = list(
            table.query_entities(
                query_filter=f"PartitionKey eq '{pk}' and conversation_id eq '{conversation_id}'",
                select=["PartitionKey", "RowKey"],
            )
        )
        for it in to_delete:
            table.delete_entity(partition_key=it["PartitionKey"], row_key=it["RowKey"])
        return len(to_delete)
    except Exception as e:
        raise HTTPException(500, f"Suppression conversation impossible: {e}")
