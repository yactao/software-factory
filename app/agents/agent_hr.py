from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.llm import get_llm
from app.retrieval import AzureSearch, in_scope, best_answers
from app.settings import get_settings
from app.utils.text import clean_markdown
from app.storage.tables import list_conversation_events


class HrAgent:
    route_name = "hr"

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

    def _contexts(self, query: str, filters: Optional[Dict[str, Any]], top: int) -> List[Dict[str, Any]]:
        s = get_settings()
        index = s.index_hr or "idx-hr"
        client = AzureSearch()
        res = client.search(index=index, query=query, filters=filters, top=top, answers=True, captions=True)
        hits = res.get("value", []) or []
        answers = best_answers(res)
        if not in_scope(hits) and not answers:
            return []
        ctx: List[Dict[str, Any]] = []
        if answers:
            best = answers[0]
            t = (best.get("text") or "").strip()
            if t:
                ctx.append({"title": "Azure AI Search — Réponse", "snippet": t, "meta": {"kind": "answer"}})
        for d in hits[:top]:
            title = d.get("title") or d.get("path") or "Document"
            caps = d.get("@search.captions") or []
            cap_text = caps[0].get("text") if caps else ""
            snippet = (cap_text if cap_text else (d.get("content") or ""))[:1000]
            ctx.append({
                "title": title,
                "snippet": snippet,
                "meta": {"id": d.get("id"), "path": d.get("path"), "score": d.get("@search.score"),
                         "reranker": d.get("@search.rerankerScore")},
            })
        return ctx

    def handle(self, req):
        hist = self._chat_history_block(req.claims, req.conversation_id)
        contexts = self._contexts(req.question, req.filters, max(1, min(req.top_k, 8)))
        if not contexts:
            return _res("Je ne trouve pas d’information RH pertinente pour cette question.", False, [], req)

        src_block = []
        for i, c in enumerate(contexts, 1):
            title = c.get("title") or (c.get("meta", {}) or {}).get("path") or f"Source {i}"
            snippet = (c.get("snippet") or "")[:2000]
            src_block.append(f"[{i}] {title}\n{snippet}")
        user = (("HISTORIQUE:\n" + hist + "\n\n") if hist else "") + f"QUESTION:\n{req.question}\n\nSOURCES:\n" + "\n\n".join(src_block)

        sys = (
            "Assistant RH interne. Réponds uniquement aux documents fournis. "
            "Sortie JSON {\"answer\":\"...\",\"uses_context\":true|false,\"used_sources\":[<indices>]}."
        )
        llm = get_llm()
        obj = llm.generate_json(user, sys, max_tokens=900, temperature=0.2)
        answer = (obj.get("answer") or "").strip() or "Réponse vide."
        uses = bool(obj.get("uses_context", False))
        used_idx = [int(x) for x in (obj.get("used_sources") or []) if str(x).isdigit()]

        docs = []
        for i in used_idx:
            if 1 <= i <= len(contexts):
                c = contexts[i - 1]
                if (c.get("meta", {}) or {}).get("kind") == "answer":
                    continue
                docs.append({
                    "id": c.get("meta", {}).get("id"),
                    "title": c.get("title"),
                    "path": c.get("meta", {}).get("path"),
                    "score": c.get("meta", {}).get("score"),
                    "reranker": c.get("meta", {}).get("reranker"),
                })
        if not docs and uses:
            for c in [c for c in contexts if (c.get("meta", {}) or {}).get("kind") != "answer"][:3]:
                docs.append({
                    "id": c.get("meta", {}).get("id"),
                    "title": c.get("title"),
                    "path": c.get("meta", {}).get("path"),
                    "score": c.get("meta", {}).get("score"),
                    "reranker": c.get("meta", {}).get("reranker"),
                })
        return _res(answer, uses, docs, req)


def _res(answer: str, uses: bool, docs: List[Dict[str, Any]], req) -> dict:
    return {"answer": answer, "uses_context": uses, "used_docs": docs, "citations": [], "conversation_id": req.conversation_id}
