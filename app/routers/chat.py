from app.models.schemas import ClearAllResult, RenameBody
from app.services.history_helpers import _chat_table_cached, _derive_title, _pk_from_claims, _save_chat_event
from ..core.security import _auth_dependency, _require_scope
from fastapi import APIRouter, Depends, HTTPException, Query
import json
from typing import Any, Dict

router = APIRouter()

@router.get("/api/chat/history")
def chat_history(conversation_id: str, claims: Dict[str, Any] = Depends(_auth_dependency)):
    _require_scope(claims)
    pk = _pk_from_claims(claims)

    table = _chat_table_cached()
    if table is None :
        raise HTTPException(500, "Table Storage indisponible.")

    filt = f"PartitionKey eq '{pk}' and conversation_id eq '{conversation_id}'"
    items = list(table.query_entities(
        query_filter=filt,
        select=["RowKey","role","route","message","timestamp_utc","meta_json"]
    ))

    items.sort(key=lambda x: x.get("RowKey",""))  # chrono

    msgs = []
    for it in items:
        meta_raw = it.get("meta_json")
        meta = {}
        if meta_raw:
            try:
                meta = json.loads(meta_raw)
            except Exception:
                meta = {"_meta_json_error": True}

        msgs.append({
            "role": it.get("role"),
            "route": it.get("route"),
            "message": it.get("message") or "",
            "timestamp_utc": it.get("timestamp_utc"),
            "meta": meta,
        })

    return {"conversation_id": conversation_id, "messages": msgs, "count": len(msgs)}

@router.get("/api/chat/list/{route_name}")
def chat_list_by_route(route_name: str, claims: Dict[str, Any] = Depends(_auth_dependency)):
    _require_scope(claims)
    pk = _pk_from_claims(claims)

    table = _chat_table_cached()
    if table is None :
        raise HTTPException(500, "Table Storage indisponible.")

    # Sécurité/escape OData sur la route
    route_filter = str(route_name).strip().replace("'", "''")

    # On lit uniquement les colonnes utiles et on filtre côté table par la route
    items = list(table.query_entities(
        query_filter=f"PartitionKey eq '{pk}' and route eq '{route_filter}'",
        select=["RowKey","conversation_id","role","route","message","timestamp_utc","meta_json"]
    ))

    if not items:
        return {"conversations": [], "count": 0}

    items.sort(key=lambda x: x.get("RowKey",""))  # ordre chrono

    summary: Dict[str, Dict[str, Any]] = {}
    for it in items:
        cid = it.get("conversation_id")
        if not cid:
            continue

        rowkey = it.get("RowKey","")
        role   = (it.get("role") or "").strip()
        route  = (it.get("route") or "").strip()
        msg    = (it.get("message") or "").strip()
        ts     = it.get("timestamp_utc") or ""

        s = summary.setdefault(cid, {
            "conversation_id": cid,
            "title": None,
            "_first_user_title": None,
            "last_activity_utc": ts,
            "last_route": route,
            "_last_rowkey": rowkey,
        })

        # met à jour "dernier message" via RowKey
        if rowkey >= s["_last_rowkey"]:
            s["_last_rowkey"] = rowkey
            s["last_activity_utc"] = ts
            s["last_route"] = route

        # Titre explicite (événement meta_json de cette même route si présent)
        meta_raw = it.get("meta_json")
        if meta_raw:
            try:
                meta = json.loads(meta_raw)
            except Exception:
                meta = {}
            if isinstance(meta, dict) and meta.get("type") == "title":
                t = str(meta.get("title") or "").strip()
                if t:
                    s["title"] = t[:200]

        # Sinon titre dérivé du 1er message user de cette route
        if not s["title"] and role == "user" and msg:
            s["_first_user_title"] = _derive_title(msg, route)

    out = []
    for cid, s in summary.items():
        title = s["title"] or s["_first_user_title"] or cid
        out.append({
            "conversation_id": cid,
            "title": title,
            "last_activity_utc": s["last_activity_utc"],
            "last_route": s["last_route"],
        })

    out.sort(key=lambda x: x.get("last_activity_utc",""), reverse=True)
    return {"conversations": out, "count": len(out)}


@router.post("/api/chat/rename")
def chat_rename(body: RenameBody, claims: Dict[str, Any] = Depends(_auth_dependency)):
    _require_scope(claims)
    t = (body.title or "").strip()
    if not t:
        raise HTTPException(400, "Titre invalide.")

    # on stocke un événement "titre" dans la conversation
    _save_chat_event(
        claims,
        conversation_id=body.conversation_id,
        role="meta",
        route="meta",
        message="",  # pas affiché
        meta={"type": "title", "title": t}
    )
    return {"ok": True, "conversation_id": body.conversation_id, "title": t}

@router.delete("/api/chat/clear")
def chat_clear(conversation_id: str, claims: Dict[str, Any] = Depends(_auth_dependency)):
    _require_scope(claims)
    pk = _pk_from_claims(claims)

    table = _chat_table_cached()
    if table is None :
        raise HTTPException(500, "Table Storage indisponible.")

    # supprime tous les messages de la conversation
    to_delete = list(table.query_entities(
        query_filter=f"PartitionKey eq '{pk}' and conversation_id eq '{conversation_id}'",
        select=["PartitionKey","RowKey"]
    ))

    for it in to_delete:
        table.delete_entity(partition_key=it["PartitionKey"], row_key=it["RowKey"])

    return {"deleted": True, "conversation_id": conversation_id}



@router.delete("/api/chat/clear-all/{route_name}", response_model=ClearAllResult)
def chat_clear_all(
    route_name: str,
    purge_entire_conversation: bool = Query(
        True,
        description="True: supprime toute la conversation (toutes routes) pour les conversations de cette route. "
                    "False: supprime uniquement les messages de la route ciblée."
    ),
    claims: Dict[str, Any] = Depends(_auth_dependency),
):
    """
    Supprime toutes les conversations de l'utilisateur pour une route donnée.

    - route_name: 'rag', 'trading', 'finance', 'search', etc.
    - purge_entire_conversation=True (défaut): supprime tous les messages (toutes routes)
      appartenant aux conversations qui contiennent au moins un message de `route_name`.
    - purge_entire_conversation=False: ne supprime que les messages dont route == route_name,
      et les éventuels événements 'meta' liés à ces conversations (titre), si présents.
    """
    _require_scope(claims)
    pk = _pk_from_claims(claims)

    table = _chat_table_cached()
    if table is None :
        raise HTTPException(500, "Table Storage indisponible.")

    route_filter = str(route_name).strip().replace("'", "''")

    # 1) Récupérer toutes les conversations impactées par cette route
    # On lit minimalement pour trouver les conversation_id
    items = list(table.query_entities(
        query_filter=f"PartitionKey eq '{pk}' and route eq '{route_filter}'",
        select=["conversation_id"]
    ))

    conv_ids = sorted({it.get("conversation_id") for it in items if it.get("conversation_id")})
    if not conv_ids:
        return ClearAllResult(
            route=route_name,
            conversations_affected=0,
            entities_deleted=0,
            purge_entire_conversation=purge_entire_conversation
        )

    deleted = 0

    if purge_entire_conversation:
        # 2A) Purge complète: supprimer tous les messages de ces conversations, toutes routes confondues
        for cid in conv_ids:
            # récupérer les RowKey à supprimer par conversation
            to_del = list(table.query_entities(
                query_filter=f"PartitionKey eq '{pk}' and conversation_id eq '{cid}'",
                select=["PartitionKey", "RowKey"]
            ))
            for it in to_del:
                table.delete_entity(partition_key=it["PartitionKey"], row_key=it["RowKey"])
                deleted += 1
    else:
        # 2B) Purge ciblée: supprimer seulement les messages de la route demandée
        for cid in conv_ids:
            # supprimer les messages de la route ciblée dans cette conversation
            to_del_route = list(table.query_entities(
                query_filter=f"PartitionKey eq '{pk}' and conversation_id eq '{cid}' and route eq '{route_filter}'",
                select=["PartitionKey", "RowKey"]
            ))
            for it in to_del_route:
                table.delete_entity(partition_key=it["PartitionKey"], row_key=it["RowKey"])
                deleted += 1

            # supprimer aussi les éventuels événements meta (titres) rattachés à cette conversation
            to_del_meta = list(table.query_entities(
                query_filter=f"PartitionKey eq '{pk}' and conversation_id eq '{cid}' and route eq 'meta'",
                select=["PartitionKey", "RowKey"]
            ))
            for it in to_del_meta:
                table.delete_entity(partition_key=it["PartitionKey"], row_key=it["RowKey"])
                deleted += 1

    return ClearAllResult(
        route=route_name,
        conversations_affected=len(conv_ids),
        entities_deleted=deleted,
        purge_entire_conversation=purge_entire_conversation
    )
