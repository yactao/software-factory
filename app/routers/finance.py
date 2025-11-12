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

def _synth_finance(question: str, rows: List[Dict[str, Any]]) -> str:
    """
    Synthèse financière adaptée au schéma MDM:
    Construit des lignes 'magasin/dept/code_magasin/GV/PV/VE_AN/montant_annuel/période/feuille/source'
    puis demande un résumé à Gemini (prompt financier existant).
    """
    def _num(x):
        try:
            return float(x) if x is not None and str(x) not in ("", "nan") else None
        except Exception:
            return None

    lines = []
    for r in rows:
        montant = r.get("montant_annuel")
        montant_n = _num(montant)
        # formatage simple, on laisse la virgule telle quelle si fournie
        periode = ""
        if r.get("period_start") or r.get("period_end"):
            periode = f"{r.get('period_start') or ''} → {r.get('period_end') or ''}"
        feuille = r.get("sheet_name")
        if feuille and r.get("sheet_index") is not None:
            feuille = f"{feuille} (#{r.get('sheet_index')})"

        lines.append(
            "MAGASIN={mag} | DEPT={dep} | CODE={code} | GV={gv} | PV={pv} | VE_AN={ve} | "
            "MONTANT_ANNUEL={montant} ({montant_num}) | PERIODE={per} | FEUILLE={feuille} | SOURCE={src}".format(
                mag=r.get("magasin") or "",
                dep=r.get("dept") or "",
                code=r.get("code_magasin") or "",
                gv=r.get("gv") if r.get("gv") is not None else "",
                pv=r.get("pv") if r.get("pv") is not None else "",
                ve=r.get("ve_an") if r.get("ve_an") is not None else "",
                montant=montant if montant is not None else "",
                montant_num=(f"{montant_n:.2f}" if isinstance(montant_n, (int, float)) else ""),
                per=periode or "",
                feuille=feuille or "",
                src=r.get("source_workbook") or ""
            )
        )

    # Totaux globaux (ils sont déjà présents dans chaque doc, on prend la première ligne si dispo)
    if rows:
        r0 = rows[0]
        totals = []
        if r0.get("total_gv") is not None:
            totals.append(f"Total GV: {r0.get('total_gv')}")
        if r0.get("total_pv") is not None:
            totals.append(f"Total PV: {r0.get('total_pv')}")
        if r0.get("total_montant_annuel") is not None:
            try:
                tma = float(r0.get("total_montant_annuel"))
                totals.append(f"Total Montant Annuel: {tma:.2f}")
            except Exception:
                totals.append(f"Total Montant Annuel: {r0.get('total_montant_annuel')}")
        if totals:
            lines.append("== TOTAUX GLOBAUX == " + " | ".join(totals))

    model = _configure_gemini_finance()
    user_msg = f"QUESTION: {question}\n\nDONNEES:\n" + "\n".join(lines[:300])  # garde jusqu'à 300 lignes max
    obj = _call_gemini_json(model, user_msg)
    return _clean_model_text(str(obj.get("answer", "")).strip() or "Réponse vide.")


@router.post("/api/finance")
def finance_api(req: FinanceQuery, claims: Dict[str, Any] = Depends(_auth_dependency)):
    _require_scope(claims)

    # LOG user
    conv_id = _save_chat_event(
        claims, req.conversation_id, role="user", route="finance",
        message=req.query,
        meta={"ville": req.ville, "client": req.client, "top": req.top}
    )

    # Recherche dans le NOUVEL index MDM
    rows = _search_finance(req.query, req.ville, req.client, req.top or 20)
    if not rows:
        payload = {
            "answer": "Aucune ligne trouvée dans l’index MDM pour cette requête.",
            "rows": [],
            "citations": [],
            "used_docs": [],
            "conversation_id": conv_id
        }
        _save_chat_event(claims, conv_id, role="assistant", route="finance",
                         message=payload["answer"], meta=payload)
        return payload

    # Synthèse adaptée MDM
    answer = _synth_finance(req.query, rows[: min(len(rows), 150)])

    # 'used_docs' lisible côté front (titre = magasin + feuille ; path = source_workbook)
    preview = rows[: min(len(rows), 60)]
    used = []
    for r in preview:
        title_parts = []
        if r.get("magasin"):
            title_parts.append(str(r.get("magasin")))
        if r.get("sheet_name"):
            title_parts.append(str(r.get("sheet_name")))
        title = " — ".join(title_parts) or (r.get("code_magasin") or "Ligne")

        used.append({
            "id": r.get("id"),
            "title": title,
            "path": r.get("source_workbook") or "",
            "meta": {
                "dept": r.get("dept"),
                "code_magasin": r.get("code_magasin"),
                "gv": r.get("gv"),
                "pv": r.get("pv"),
                "ve_an": r.get("ve_an"),
                "montant_annuel": r.get("montant_annuel"),
                "period_start": r.get("period_start"),
                "period_end": r.get("period_end"),
            }
        })

    payload = {
        "answer": answer,
        "rows": rows[: min(len(rows), 300)],
        "citations": [],
        "used_docs": used,
        "conversation_id": conv_id
    }
    _save_chat_event(claims, conv_id, role="assistant", route="finance",
                     message=answer, meta=payload)
    return payload
