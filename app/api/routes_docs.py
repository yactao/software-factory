from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any, List, Set

from app.security.auth import require_user
from app.storage.blob import resolve_blob_with_fallbacks, make_sas_url
from app.storage.tables import (
    get_chat_table,
    list_conversation_events,
    delete_conversation,
)

router = APIRouter()


# ---------- SAS blob ----------

@router.get("/sas")
def get_sas(
    path: str = Query(..., description="Chemin du blob (peut se terminer par .pdf ou .docx)"),
    ttl: int = Query(5, ge=1, le=60, description="Durée du SAS en minutes"),
    claims=Depends(require_user),
):
    # Résout (container, blob) en testant .pdf <-> .docx et plusieurs conteneurs
    container, blob = resolve_blob_with_fallbacks(path, containers=None, try_docx_pdf=True)
    url = make_sas_url(container, blob, minutes=ttl)
    return {
        "url": url,
        "container": container,
        "blob": blob,
        "expires_in_minutes": ttl,
    }


# ---------- Chat history / list / rename / clear ----------

class RenameBody(BaseModel):
    conversation_id: str
    title: str


@router.get("/chat/history")
def chat_history(conversation_id: str, claims=Depends(require_user)):
    # Retourne tous les messages d’une conversation (rôle, route, message, meta)
    events = list_conversation_events(claims, conversation_id)
    return {"conversation_id": conversation_id, "messages": events, "count": len(events)}


@router.get("/chat/list/{route_name}")
def chat_list_by_route(route_name: str, claims=Depends(require_user)):
    """
    Liste les conversations d'une route donnée (par utilisateur).
    - Filtre par 'route' (rag, finance, trading, hr, search, etc.)
    - Reconstruit le titre à partir du 1er message user si aucun titre explicite n'a été posé
      via un événement meta {"type": "title", "title": "..."}.
    - Trie par dernière activité (tolérant aux timestamps manquants/None).
    """
    # Récup client Table
    table = get_chat_table()

    # PartitionKey = <tenant>|<user>
    pk = f"{claims.get('tid','')}|{claims.get('sub') or claims.get('oid','')}"
    route_filter = (route_name or "").replace("'", "''")

    # Lecture minimale des colonnes utiles
    try:
        items = list(
            table.query_entities(
                query_filter=f"PartitionKey eq '{pk}' and route eq '{route_filter}'",
                select=["RowKey", "conversation_id", "role", "route", "message", "timestamp_utc", "meta_json"],
            )
        )
    except Exception as e:
        raise HTTPException(500, f"Lecture Table Storage impossible: {e}")

    if not items:
        return {"conversations": [], "count": 0}

    # Tri chronologique via RowKey (new_rowkey() est triable dans le temps)
    items.sort(key=lambda x: x.get("RowKey", ""))

    summary: Dict[str, Dict[str, Any]] = {}
    for it in items:
        cid = it.get("conversation_id")
        if not cid:
            continue

        rowkey = it.get("RowKey", "")
        ts_utc = it.get("timestamp_utc")  # peut être None
        role = (it.get("role") or "").strip()
        msg = (it.get("message") or "").strip()
        rt = (it.get("route") or "").strip()

        # Titre explicite depuis meta_json si présent (type='title')
        title_from_meta: Optional[str] = None
        meta_raw = it.get("meta_json")
        if meta_raw:
            try:
                meta_obj = json.loads(meta_raw)
                if isinstance(meta_obj, dict) and meta_obj.get("type") == "title":
                    t = str(meta_obj.get("title") or "").strip()
                    if t:
                        title_from_meta = t[:200]
            except Exception:
                pass

        s = summary.setdefault(
            cid,
            {
                "conversation_id": cid,
                "title": None,                 # titre explicite via meta
                "_first_user_title": None,     # fallback: 1er message user
                "last_activity_utc": None,     # str|None
                "last_route": None,
                "_last_rowkey": "",            # pour trier si timestamp vide
            },
        )

        # Met à jour le titre explicite si on en voit un
        if title_from_meta:
            s["title"] = title_from_meta

        # Met à jour le "dernier message" par RowKey
        if rowkey >= (s["_last_rowkey"] or ""):
            s["_last_rowkey"] = rowkey
            # last_activity_utc peut être None → on n'écrase que si on a une valeur ou si rien n'existait
            s["last_activity_utc"] = ts_utc if (ts_utc or s.get("last_activity_utc") is None) else s["last_activity_utc"]
            s["last_route"] = rt

        # Titre reconstruit depuis le premier message user
        if not s["title"] and role == "user" and msg:
            first_line = " ".join(msg.splitlines()).strip()
            first = first_line[:60] if first_line else "Conversation"
            prefix = "📄 " if route_name == "rag" else ("💹 " if route_name == "finance" else "💬 ")
            s["_first_user_title"] = f"{prefix}{first}"

    # Construit la sortie
    out: List[Dict[str, Any]] = []
    for cid, s in summary.items():
        title = s["title"] or s["_first_user_title"] or cid
        out.append(
            {
                "conversation_id": cid,
                "title": title,
                # Tolérant aux None (front attend string)
                "last_activity_utc": s.get("last_activity_utc") or "",
                "last_route": s.get("last_route") or route_name,
                # Optionnel : utile si tu veux trier côté front aussi
                "_last_rowkey": s.get("_last_rowkey") or "",
            }
        )

    # Tri robuste : si timestamp absent → on tombe sur RowKey
    out.sort(
        key=lambda x: ((x.get("last_activity_utc") or ""), (x.get("_last_rowkey") or "")),
        reverse=True,
    )

    # Retire le champ interne si tu ne veux pas l'exposer
    for r in out:
        r.pop("_last_rowkey", None)

    return {"conversations": out, "count": len(out)}

@router.post("/chat/rename")
def chat_rename(body: RenameBody, claims=Depends(require_user)):
    """
    Pour rester simple on n’écrit pas un event 'title' dédié ici,
    mais tu peux le faire via save_chat_event(...) route='meta' si besoin.
    """
    if not (body.conversation_id and body.title.strip()):
        raise HTTPException(400, "Titre invalide.")
    # Ici, on pourrait écrire un meta event. On retourne simplement l'info.
    return {"ok": True, "conversation_id": body.conversation_id, "title": body.title.strip()}


@router.delete("/chat/clear")
def chat_clear(conversation_id: str, claims=Depends(require_user)):
    count = delete_conversation(claims, conversation_id)
    return {"deleted": True, "conversation_id": conversation_id, "items": count}


# ---------- Suppression de TOUTES les conversations d'une route donnée ----------

@router.delete("/chat/clear-all")
def chat_clear_all_by_route(
    route: str = Query(..., description="Nom de route: rag | trading | hr | finance | vision"),
    claims=Depends(require_user),
):
    """
    Supprime toutes les conversations d'une route donnée pour l'utilisateur courant.
    Implémentation: on liste les entités (route, PartitionKey), regroupe par conversation_id,
    puis on appelle delete_conversation sur chacune.
    """
    table = get_chat_table()
    pk = f"{claims.get('tid','')}|{claims.get('sub') or claims.get('oid','')}"
    route_filter = route.replace("'", "''")

    items = list(
        table.query_entities(
            query_filter=f"PartitionKey eq '{pk}' and route eq '{route_filter}'",
            select=["conversation_id"],
        )
    )
    if not items:
        return {"deleted": True, "route": route, "conversations": [], "count": 0}

    conv_ids: Set[str] = {it.get("conversation_id") for it in items if it.get("conversation_id")}
    deleted = 0
    for cid in conv_ids:
        try:
            deleted += delete_conversation(claims, cid)
        except Exception:
            # on continue même si une conv échoue
            continue

    return {"deleted": True, "route": route, "conversations": list(conv_ids), "items": deleted}
