import re, json, random, datetime as _dt
from typing import Dict, Any, List, Optional
from azure.data.tables import TableClient
from azure.core.pipeline.policies import RetryPolicy
from azure.data.tables import TableServiceClient
from azure.core.exceptions import ResourceExistsError
from fastapi import HTTPException

from app.core.config import (
    AZURE_STORAGE_CONNECTION_STRING, ACCOUNT_NAME, ACCOUNT_KEY,
    CHAT_BACKEND, CHAT_TABLE
)

# Caractères interdits dans PartitionKey/RowKey
INVALID_KEY_CHARS_RE = re.compile(r"[#?/\\\x00-\x1F]")

# Caches globaux
_TABLE_CLIENT = None
_CHAT_TABLE_CLIENT = None
TABLE_READY = False

# ---------------------------
# Utilitaires clés/formatage
# ---------------------------
def _safe_key(s: str) -> str:
    if not s:
        return ""
    return re.sub(INVALID_KEY_CHARS_RE, "_", str(s))[:900]

def _pk_from_claims(claims: Dict[str, Any]) -> str:
    # AAD met parfois aussi l'identifiant dans "oid" ; on le prend en secours
    tid = str(claims.get("tid") or "").strip()
    sub = str(claims.get("sub") or claims.get("oid") or "").strip()
    # séparateur sûr (| ou _ conviennent)
    return _safe_key(f"{tid}|{sub}")

def _rk_now() -> str:
    return _dt.datetime.utcnow().strftime("%Y%m%d%H%M%S%f") + f"-{random.randint(1000,9999)}"

def _pack_meta(meta: Optional[Dict[str, Any]], limit_chars: int = 32000) -> str:
    try:
        if not meta:
            return "{}"
        s = json.dumps(meta, ensure_ascii=False)
        if len(s) <= limit_chars:
            return s
        slim: Dict[str, Any] = {"truncated": True}
        if isinstance(meta, dict):
            if "answer" in meta:
                slim["answer"] = str(meta.get("answer", ""))[:8000]
            if "used_docs" in meta and isinstance(meta["used_docs"], list):
                uds = meta["used_docs"][:20]
                slim["used_docs"] = [
                    {"title": str((d or {}).get("title", ""))[:200],
                     "path": str((d or {}).get("path", ""))[:400]}
                    for d in uds
                ]
            if "rows" in meta and isinstance(meta["rows"], list):
                slim["rows_preview"] = meta["rows"][:10]
                slim["rows_total"] = len(meta["rows"])
        s = json.dumps(slim, ensure_ascii=False)
        return s[:limit_chars]
    except Exception:
        return "{}"

# ---------------------------
# Table service & table chat
# ---------------------------
def _table_service_client_cached() -> TableServiceClient:
    global _TABLE_CLIENT
    if _TABLE_CLIENT is not None:
        return _TABLE_CLIENT

    try:
        if AZURE_STORAGE_CONNECTION_STRING:
            conn = AZURE_STORAGE_CONNECTION_STRING
        elif ACCOUNT_NAME and ACCOUNT_KEY:
            conn = (
                f"DefaultEndpointsProtocol=https;"
                f"AccountName={ACCOUNT_NAME};"
                f"AccountKey={ACCOUNT_KEY};"
                f"EndpointSuffix=core.windows.net"
            )
        else:
            raise RuntimeError(
                "Config Table Storage manquante (AZURE_STORAGE_CONNECTION_STRING ou ACCOUNT_NAME/KEY)."
            )

        _TABLE_CLIENT = TableServiceClient.from_connection_string(
            conn,
            retry_policy=RetryPolicy(total_retries=2, retry_backoff_factor=0.5),
        )
        return _TABLE_CLIENT
    except Exception as e:
        raise HTTPException(500, f"Erreur TableService: {e}")


# ---------------------------
# Titre dérivé premier message
# ---------------------------
def _derive_title(message: str, route: str) -> str:
    if not message:
        return route
    first = message.strip().split("\n")[0]
    first = re.sub(r"\s+", " ", first).strip()
    return (first[:80] or route)

# ---------------------------
# Sauvegarde & lectures
# ---------------------------

def _gen_conversation_id() -> str:
    ts = _dt.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    return f"conv-{ts}-{random.randint(1000,9999)}"

def _derive_title(message: str, route: str) -> str:
    # 1re ligne non vide, nettoyée, tronquée
    raw = (message or "").strip().splitlines()
    first = next((l.strip() for l in raw if l.strip()), "")
    first = re.sub(r"\s+", " ", first)[:60] or "Nouvelle conversation"
    prefix = "📄 " if route == "rag" else ("💹 " if route == "finance" else "💬 ")
    return f"{prefix}{first}"


def _chat_table_cached():
    """Retourne le TableClient de la table, sans bloquer l'app si ça échoue."""
    global _CHAT_TABLE_CLIENT, TABLE_READY

    if CHAT_BACKEND != "table":
        return None

    if _CHAT_TABLE_CLIENT is not None and TABLE_READY:
        return _CHAT_TABLE_CLIENT

    try:
        svc = _table_service_client_cached()
        # Essaye d'obtenir la table; création lazy mais pas à chaque requête
        try:
            _CHAT_TABLE_CLIENT = svc.get_table_client(CHAT_TABLE)
            _ = list(_CHAT_TABLE_CLIENT.list_entities(results_per_page=1))  # ping ultra court
            TABLE_READY = True
            return _CHAT_TABLE_CLIENT
        except Exception:
            # Tentative unique de création
            svc.create_table_if_not_exists(CHAT_TABLE)
            _CHAT_TABLE_CLIENT = svc.get_table_client(CHAT_TABLE)
            TABLE_READY = True
            return _CHAT_TABLE_CLIENT
    except Exception as e:
        # IMPORTANT: on bascule silencieusement en mémoire
        print(f"[chat-history] Table Storage indisponible, fallback mémoire: {e}")
        TABLE_READY = False
        return None

def _save_chat_event(
    claims: Dict[str, Any],
    conversation_id: Optional[str],
    role: str,
    route: str,
    message: str,
    meta: Optional[Dict[str, Any]] = None
) -> str:
    conv = conversation_id or _gen_conversation_id()
    ts_iso = _dt.datetime.utcnow().isoformat() + "Z"

    table = _chat_table_cached()
    if table is None or not TABLE_READY:
        raise HTTPException(500, "Table Storage indisponible.")

    table.upsert_entity({
        "PartitionKey": _pk_from_claims(claims),
        "RowKey": _rk_now(),                         # ordre chrono
        "conversation_id": conv,
        "role": role,                                # 'user' | 'assistant' | 'meta'
        "route": route,                              # 'rag' | 'finance' | 'meta'
        "message": (message or "")[:32000],          # le texte affichable
        "meta_json": _pack_meta(meta),               # données additionnelles
        "timestamp_utc": ts_iso,
        "tenant_id": claims.get("tid"),
        "user_id": claims.get("sub"),
        "username": claims.get("preferred_username"),
    })

    return conv

def _get_last_qna_pairs(
    claims: Dict[str, Any],
    conversation_id: Optional[str],
    route: str = "rag",
    max_pairs: int = 3,
) -> list[dict]:
    if not conversation_id:
        return []
    table = _chat_table_cached()
    if table is None or not TABLE_READY:
        return []
    pk = _pk_from_claims(claims)
    items = list(table.query_entities(
        query_filter=f"PartitionKey eq '{pk}' and conversation_id eq '{conversation_id}'",
        select=["RowKey","role","route","message"]
    ))
    items.sort(key=lambda x: x.get("RowKey",""))
    msgs = [it for it in items if (it.get("route") == route and it.get("role") in ("user","assistant"))]
    pairs, pending_user = [], None
    for it in msgs:
        role = it.get("role"); msg = (it.get("message") or "")
        if role == "user":
            pending_user = msg
        elif role == "assistant" and pending_user is not None:
            pairs.append({"user": pending_user, "assistant": msg})
            pending_user = None
    return pairs[-max_pairs:]

def _get_recent_chat_context(
    claims: Dict[str, Any],
    conversation_id: Optional[str],
    route: str = "trading",
    max_turns: int = 6,
    max_chars: int = 1200
) -> str:
    if CHAT_BACKEND not in {"table", "azure_table"}:
        return ""
    if not conversation_id:
        return ""

    table = _chat_table_cached()
    if table is None or not TABLE_READY:
        return ""

    pk = _pk_from_claims(claims)
    conv = _safe_key(conversation_id or "default")

    try:
        rows = list(
            table.query_entities(
                query_filter=f"PartitionKey eq '{pk}' and conversation_id eq '{conv}' and route eq '{route}'",
                select=["RowKey", "role", "message"],
            )
        )
    except Exception:
        return ""

    rows.sort(key=lambda r: r.get("RowKey", ""))

    buf: List[str] = []
    for r in rows[-(max_turns * 2):]:
        role = (r.get("role") or "").strip().upper()
        msg = (r.get("message") or "").strip()
        if role in {"USER", "ASSISTANT"} and msg:
            buf.append(f"{role[0]}: {msg}")

    text = "\n".join(buf).strip()
    if len(text) > max_chars:
        text = text[-max_chars:]
    return text

def get_last_vision_file_path(claims: dict, conversation_id: str) -> Optional[str]:
    """Récupère le dernier meta.vision_file_path sur la conv."""
    table: TableClient = _chat_table_cached()
    if not table: return None
    pk = _pk_from_claims(claims)
    rows = list(table.query_entities(
        query_filter=f"PartitionKey eq '{pk}' and conversation_id eq '{conversation_id}' and route eq 'vision'",
        select=["RowKey", "meta_json"]))
    rows.sort(key=lambda r: r.get("RowKey",""))
    for r in reversed(rows):
        try:
            meta = r.get("meta_json")
            if not meta: continue
            import json
            m = json.loads(meta)
            p = (m or {}).get("vision_file_path")
            if p: return p
        except Exception:
            pass
    return None

def get_last_annotated_path(claims: dict, conversation_id: str) -> Optional[str]:
    table: TableClient = _chat_table_cached()
    if not table: return None
    pk = _pk_from_claims(claims)
    rows = list(table.query_entities(
        query_filter=f"PartitionKey eq '{pk}' and conversation_id eq '{conversation_id}' and route eq 'vision'",
        select=["RowKey", "meta_json"]))
    rows.sort(key=lambda r: r.get("RowKey",""))
    for r in reversed(rows):
        try:
            import json
            m = json.loads(r.get("meta_json") or "{}")
            p = (m or {}).get("vision_annotated_blob_path")
            if p: return p
        except Exception:
            pass
    return None

def delete_vision_for_conversation(claims: dict, conversation_id: str) -> int:
    """Supprime tous les blobs du prefix pk/conv_id/*."""
    from app.services.blob_vision import delete_prefix
    pk = _pk_from_claims(claims)
    return delete_prefix(f"{pk}/{conversation_id}/")