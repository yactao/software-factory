from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.llm import get_llm
from app.retrieval import AzureSearch, in_scope
from app.settings import get_settings
from app.utils.text import clean_markdown, clean_trading_text
from app.storage.tables import list_conversation_events


class TradingAgent:
    route_name = "trading"

    def _chat_history_block(
        self, claims: Dict[str, Any], conversation_id: Optional[str], max_turns: int = 6, max_chars: int = 1200
    ) -> str:
        if not conversation_id:
            return ""
        events = list_conversation_events(claims, conversation_id, select=["RowKey", "role", "route", "message"])
        msgs = [(e["role"], e["message"]) for e in events if e.get("route") == self.route_name]
        lines: List[str] = []
        for role, msg in msgs[-12:]:
            tag = "U" if role == "user" else "A"
            m = clean_trading_text(msg or "")
            lines.append(f"{tag}: {m}")
        text = "\n".join(lines).strip()
        if len(text) > max_chars:
            text = text[-max_chars:]
        return text

    def _contexts_from_search(self, query: str, filters: Optional[Dict[str, Any]], top: int) -> List[Dict[str, Any]]:
        s = get_settings()
        index = s.index_trading or "idx-oil-demo"
        if filters and "index_name" in (filters or {}):
            index = filters["index_name"] or index

        client = AzureSearch()
        res = client.search(index=index, query=query, filters=filters, top=top, answers=False, captions=True)
        hits = res.get("value", []) or []
        if not in_scope(hits):
            return []
        contexts: List[Dict[str, Any]] = []
        for d in hits[:top]:
            title = d.get("title") or d.get("source_path") or "Document"
            caps = d.get("@search.captions") or []
            cap_text = caps[0].get("text") if caps else ""
            snippet = (cap_text + "\n" + (d.get("content") or ""))[:1800]
            contexts.append({
                "title": title,
                "snippet": snippet,
                "meta": {
                    "id": d.get("id"),
                    "path": d.get("source_path"),
                    "score": d.get("@search.score"),
                    "reranker": d.get("@search.rerankerScore"),
                },
            })
        return contexts

    def handle(self, req):
        hist = self._chat_history_block(req.claims, req.conversation_id)
        contexts = self._contexts_from_search(req.question, req.filters, max(1, min(req.top_k, 8)))

        if not contexts:
            return _result("Je ne sais pas. Aucune information suffisamment pertinente dans les documents indexés.", False, [], req)

        src_block = []
        for i, c in enumerate(contexts, 1):
            title = c.get("title") or (c.get("meta", {}) or {}).get("path") or f"Source {i}"
            snippet = (c.get("snippet") or "")[:2000]
            src_block.append(f"[{i}] {title}\n{snippet}")

        hist_block = (("HISTORIQUE (même conversation):\n" + hist + "\n\n") if hist else "")
        user = hist_block + f"QUESTION:\n{req.question}\n\nSOURCES:\n" + "\n\n".join(src_block)

        sys_rules = (
            "Assistant spécialisé trading & conformité. "
            "Réponds STRICTEMENT aux SOURCES; si l’info n’y est pas: dis 'Je ne sais pas'. "
            "Sortie JSON: {\"answer\":\"<texte brut, sans markdown, sans puces>\",\"uses_context\":true|false,\"used_sources\":[<indices>]}."
        )

        llm = get_llm(preferred=None)
        obj = llm.generate_json(user, sys_rules, max_tokens=1100, temperature=0.2)

        answer = clean_trading_text((obj.get("answer") or "").strip() or "Réponse vide.")
        uses = bool(obj.get("uses_context", False))
        used_idx = [int(x) for x in (obj.get("used_sources") or []) if str(x).isdigit()]

        docs = []
        for i in used_idx:
            if 1 <= i <= len(contexts):
                c = contexts[i - 1]
                docs.append({
                    "id": c.get("meta", {}).get("id"),
                    "title": c.get("title"),
                    "path": c.get("meta", {}).get("path"),
                    "score": c.get("meta", {}).get("score"),
                    "reranker": c.get("meta", {}).get("reranker"),
                })
        if not docs and uses:
            for c in contexts[:3]:
                docs.append({
                    "id": c.get("meta", {}).get("id"),
                    "title": c.get("title"),
                    "path": c.get("meta", {}).get("path"),
                    "score": c.get("meta", {}).get("score"),
                    "reranker": c.get("meta", {}).get("reranker"),
                })

        return _result(answer, uses, docs, req)


def _result(answer: str, uses: bool, docs: List[Dict[str, Any]], req) -> dict:
    return {
        "answer": answer,
        "uses_context": uses,
        "used_docs": docs,
        "citations": [],
        "conversation_id": req.conversation_id,
    }
