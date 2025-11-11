# app/routers/finance.py
import json
import re
from typing import List, Dict, Any
from fastapi import APIRouter, Depends

from app.utils.snippets import _to_float_str_fr  # si utilisé ailleurs
from ..core.security import _auth_dependency, _require_scope
from ..models.schemas import FinanceQuery
from ..services.history_helpers import _save_chat_event
from ..services.search_azure import _search_finance
from ..services.gemini_base import _configure_gemini_finance, _call_gemini_json
from ..utils.text_clean import _clean_model_text

router = APIRouter()


def _strip_code_fences(s: str) -> str:
    """Retire les fences ``` ou ```json ... ``` en début/fin."""
    if not isinstance(s, str):
        return s
    s = s.strip()
    s = re.sub(r"^```(?:json)?\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s*```$", "", s)
    return s.strip()


def _extract_answer_text(raw: Any) -> str:
    """
    Normalise ce que renvoie Gemini pour obtenir **du texte simple**.
    Accepte dict, str JSON, str texte. Gère les \n échappés et les code fences.
    """
    if raw is None:
        return "Réponse vide."

    # 1) Si c’est déjà un dict (cas fréquent avec _call_gemini_json)
    if isinstance(raw, dict):
        for k in ("answer", "text", "content", "output"):
            if isinstance(raw.get(k), str) and raw.get(k).strip():
                return _clean_model_text(raw[k]).replace("\\n", "\n").strip()
        # Dernier recours: stringifier tout
        return _clean_model_text(json.dumps(raw, ensure_ascii=False)).strip()

    # 2) Si c’est une chaîne
    if isinstance(raw, str):
        s = _strip_code_fences(raw)
        # Essayer de parser du JSON contenu dans la chaîne
        maybe_json = s
        # Si la chaîne contient explicitement un objet JSON
        if "{" in s and "}" in s:
            try:
                obj = json.loads(s)
                if isinstance(obj, dict):
                    for k in ("answer", "text", "content", "output"):
                        if isinstance(obj.get(k), str) and obj.get(k).strip():
                            return _clean_model_text(obj[k]).replace("\\n", "\n").strip()
                    # sinon, re-dumper proprement
                    return _clean_model_text(json.dumps(obj, ensure_ascii=False)).strip()
                # liste -> texte
                if isinstance(obj, list):
                    return _clean_model_text("\n".join(map(str, obj))).strip()
            except Exception:
                # pas un JSON valide: continuer
                pass

        # Pas du JSON: on nettoie et on remplace \n échappés
        return _clean_model_text(s).replace("\\n", "\n").strip()

    # 3) Autres types: cast en str
    return _clean_model_text(str(raw)).replace("\\n", "\n").strip()


def _synth_finance(question: str, tables: List[Dict[str, Any]]) -> str:
    model = _configure_gemini_finance()

    # Compacte les infos utiles (noms de colonnes + résumé numérique) pour chaque table
    lines: List[str] = []
    for t in tables:
        cols = ", ".join(
            [c.get("name", "") for c in (t.get("schema") or []) if c.get("name")]
        )[:300]

        nums = []
        for n in (t.get("numeric_summary") or [])[:6]:
            try:
                nums.append(
                    f"{n.get('column')} sum={n.get('sum')} "
                    f"mean={round(float(n.get('mean', 0.0)), 2)} "
                    f"min={n.get('min')} max={n.get('max')}"
                )
            except Exception:
                continue
        numline = "; ".join(nums)

        lines.append(
            f"Fichier={t.get('file_name')} | Feuille={t.get('sheet_name')} | "
            f"Lignes={t.get('row_count')} | Colonnes={t.get('column_count')} | "
            f"Colonnes_noms={cols} | Resume_numerique={numline} | CSV={t.get('csv_blob_url') or ''}"
        )

    user_msg = f"QUESTION: {question}\n\nTABLES:\n" + "\n".join(lines)

    # Peut renvoyer un dict ou une chaîne JSON: on normalise
    raw = _call_gemini_json(model, user_msg)
    answer_txt = _extract_answer_text(raw)

    # Sécurité finale
    return answer_txt or "Réponse vide."


@router.post("/api/finance")
def finance_api(req: FinanceQuery, claims: dict = Depends(_auth_dependency)):
    _require_scope(claims)

    conv_id = _save_chat_event(
        claims,
        req.conversation_id,
        role="user",
        route="finance",
        message=req.query,
        meta={"ville": req.ville, "client": req.client, "top": req.top},
    )

    rows = _search_finance(req.query, req.ville, req.client, req.top or 20)
    if not rows:
        payload = {
            "answer": "Aucune feuille pertinente trouvée dans l’index financier.",
            "rows": [],
            "citations": [],
            "used_docs": [],
            "conversation_id": conv_id,
        }
        _save_chat_event(
            claims, conv_id,
            role="assistant", route="finance",
            message=payload["answer"], meta=payload
        )
        return payload

    # Synthèse pilotée par schema + numeric_summary
    answer = _synth_finance(req.query, rows[: min(len(rows), 100)])

    # used_docs adaptés au nouveau schéma
    used = []
    for r in rows[: min(len(rows), 50)]:
        title = f"{r.get('file_name') or 'Fichier'} › {r.get('sheet_name') or 'Feuille'}"
        path = r.get("csv_blob_url")  # si privé: générer SAS ici
        used.append({
            "id": r.get("id"),
            "title": title,
            "path": path,
            "meta": {
                "sheet_index": r.get("sheet_index"),
                "row_count": r.get("row_count"),
                "column_count": r.get("column_count"),
            },
        })

    payload = {
        "answer": answer,                     # ← maintenant du texte propre
        "rows": rows[: min(len(rows), 200)],  # feuilles pertinentes
        "citations": [],
        "used_docs": used,
        "conversation_id": conv_id,
    }
    _save_chat_event(
        claims, conv_id,
        role="assistant", route="finance",
        message=answer, meta=payload
    )
    return payload
