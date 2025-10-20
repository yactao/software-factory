from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.llm import get_llm
from app.retrieval import AzureSearch
from app.settings import get_settings
from app.storage.tables import list_conversation_events
from app.utils.text import clean_markdown


class TableAgent:
    route_name = "finance"

    def _chat_history_block(self, claims, conversation_id, max_turns: int = 6, max_chars: int = 1200) -> str:
        if not conversation_id:
            return ""
        events = list_conversation_events(claims, conversation_id, select=["RowKey", "role", "route", "message"])
        msgs = [(e["role"], e["message"]) for e in events if e.get("route") == self.route_name]
        lines = []
        for role, msg in msgs[-12:]:
            tag = "U" if role == "user" else "A"
            lines.append(f"{tag}: {clean_markdown(msg or '')}")
        text = "\n".join(lines).strip()
        if len(text) > max_chars:
            text = text[-max_chars:]
        return text

    def _rows_from_search(self, query: str, filters: Optional[Dict[str, Any]], top: int) -> List[Dict[str, Any]]:
        s = get_settings()
        index = s.index_finance or "idx-finance-csv"
        client = AzureSearch()
        # simple query; pas de captions/answers sur un index tabulaire
        res = client.search(index=index, query=query or "*", filters=filters, top=top, answers=False, captions=False,
                            query_type="simple",
                            select="row_id,Date,N_Piece,Client,Ville,Nature,Compte,Montant_HT,TVA_20,Montant_TTC,Compte_Tiers")
        return res.get("value", []) or []

    def handle(self, req):
        hist = self._chat_history_block(req.claims, req.conversation_id)
        rows = self._rows_from_search(req.question, req.filters, max(1, min(req.top_k, 50)))

        if not rows:
            return _res("Aucune écriture trouvée pour cette requête.", False, [], req)

        # Fabriquer un texte tabulaire léger comme contexte
        lines = []
        for r in rows[:100]:
            lines.append(
                f"N_Piece={r.get('N_Piece','')} | Date={r.get('Date','')} | Client={r.get('Client','')} | "
                f"Ville={r.get('Ville','')} | Nature={r.get('Nature','')} | Compte={r.get('Compte','')} | "
                f"Montant_HT={r.get('Montant_HT','')} | TVA_20={r.get('TVA_20','')} | Montant_TTC={r.get('Montant_TTC','')} | "
                f"Compte_Tiers={r.get('Compte_Tiers','')}"
            )

        user = (("HISTORIQUE:\n" + hist + "\n\n") if hist else "") + \
               f"QUESTION: {req.question}\n\nDONNEES:\n" + "\n".join(lines)

        sys = (
            "Assistant financier. Réponds en TEXTE BRUT (pas de markdown, pas de puces). "
            "Sortie JSON stricte: {\"answer\":\"<résumé 2-4 phrases + totaux si calculables>\",\"uses_context\":true}."
        )
        llm = get_llm(preferred=None)
        obj = llm.generate_json(user, sys, max_tokens=900, temperature=0.2)

        answer = (obj.get("answer") or "").strip() or "Réponse vide."
        uses = bool(obj.get("uses_context", True))
        # used_docs = aperçu des premières lignes retournées
        used = [{"id": r.get("row_id"), "title": r.get("N_Piece") or (r.get("Date") or "Ligne"), "path": r.get("Client") or "",
                 "score": None, "reranker": None} for r in rows[:30]]

        return _res(answer, uses, used, req)


def _res(answer: str, uses: bool, docs: List[Dict[str, Any]], req) -> dict:
    return {"answer": answer, "uses_context": uses, "used_docs": docs, "citations": [], "conversation_id": req.conversation_id}
