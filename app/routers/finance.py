from app.utils.snippets import _to_float_str_fr
from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from ..core.security import _auth_dependency, _require_scope
from ..models.schemas import FinanceQuery
from ..services.history_helpers import _save_chat_event
from ..services.search_azure import _search_finance
from ..services.gemini_base import _configure_gemini_finance, _call_gemini_json
from ..utils.text_clean import _clean_model_text

router = APIRouter()

def _synth_finance(question: str, rows: List[Dict[str, Any]]) -> str:
    lines = []
    for r in rows:
        ht, tva, ttc = r.get("Montant_HT"), r.get("TVA_20"), r.get("Montant_TTC")
        ht_n, tva_n, ttc_n = _to_float_str_fr(ht), _to_float_str_fr(tva), _to_float_str_fr(ttc)
        lines.append(
            f"N_Piece={r.get('N_Piece') or ''} | Date={r.get('Date') or ''} | Client={r.get('Client') or ''} | "
            f"Ville={r.get('Ville') or ''} | Nature={r.get('Nature') or ''} | Compte={r.get('Compte') or ''} | "
            f"Montant_HT={ht or ''} ({ht_n or ''}) | TVA_20={tva or ''} ({tva_n or ''}) | Montant_TTC={ttc or ''} ({ttc_n or ''}) | Compte_Tiers={r.get('Compte_Tiers') or ''}"
        )

    model = _configure_gemini_finance()
    user_msg = f"QUESTION: {question}\n\nDONNEES:\n" + "\n".join(lines)
    obj = _call_gemini_json(model, user_msg)
    return _clean_model_text(str(obj.get("answer", "")).strip() or "Réponse vide.")


@router.post("/api/finance")
def finance_api(req: FinanceQuery, claims: dict = Depends(_auth_dependency)):
    _require_scope(claims)
    conv_id = _save_chat_event(claims, req.conversation_id, role="user", route="finance", message=req.query, meta={"ville": req.ville, "client": req.client, "top": req.top})

    rows = _search_finance(req.query, req.ville, req.client, req.top or 20)
    if not rows:
        payload = {"answer": "Aucune écriture trouvée pour cette requête.", "rows": [], "citations": [], "used_docs": [], "conversation_id": conv_id}
        _save_chat_event(claims, conv_id, role="assistant", route="finance", message=payload["answer"], meta=payload)
        return payload

    answer = _synth_finance(req.query, rows[: min(len(rows), 100)])
    used = [{"id": r.get("row_id"), "title": r.get("N_Piece") or (r.get("Date") or "Ligne"), "path": r.get("Client") or "",
             "meta": {"Date": r.get("Date"), "Ville": r.get("Ville"), "Nature": r.get("Nature")}} for r in rows[: min(len(rows), 50)]]

    payload = {"answer": answer, "rows": rows[: min(len(rows), 200)], "citations": [], "used_docs": used, "conversation_id": conv_id}
    _save_chat_event(claims, conv_id, role="assistant", route="finance", message=answer, meta=payload)
    return payload
