# app/agents/agent_doc.py
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.llm import get_llm
from app.retrieval import AzureSearch, in_scope, best_answers
from app.settings import get_settings
from app.utils.text import clean_markdown, preview
from app.storage.tables import list_conversation_events


class DocAgent:
    route_name = "rag"

    def _chat_history_block(
        self,
        claims: Dict[str, Any],
        conversation_id: Optional[str],
        max_turns: int = 6,
        max_chars: int = 1200,
    ) -> str:
        """Construit un bloc 'HISTORIQUE' compact U:/A: comme dans Trading."""
        if not conversation_id:
            return ""

        # ✅ plus de paramètre 'select' ici
        events = list_conversation_events(claims, conversation_id)

        # garder seulement cette route
        msgs: List[tuple[str, str]] = []
        for e in events:
            if e.get("route") == self.route_name:
                role = e.get("role")
                msg = e.get("message") or ""
                if role in ("user", "assistant"):
                    msgs.append((role, msg))

        # prendre les derniers tours (user/assistant)
        # max_turns s'entend par pair U/A (donc 2 * max_turns messages)
        lines: List[str] = []
        for role, msg in msgs[-(2 * max_turns):]:
            tag = "U" if role == "user" else "A"
            m = clean_markdown(msg)
            lines.append(f"{tag}: {m}")

        text = "\n".join(lines).strip()
        if len(text) > max_chars:
            text = text[-max_chars:]
        return text

    def _contexts_from_search(self, query: str, filters: Optional[Dict[str, Any]], top: int) -> List[Dict[str, Any]]:
        s = get_settings()
        index = s.index_chunks or "idx-rag-chunks"

        if filters and "index_name" in filters:
            index = filters["index_name"] or index

        client = AzureSearch()
        res = client.search(
            index=index,
            query=query,
            filters=filters or {},
            top=top,
            answers=True,
            captions=True,
        )
        hits = res.get("value", []) or []
        answers = best_answers(res)

        if not in_scope(hits) and not answers:
            return []

        contexts: List[Dict[str, Any]] = []

        # Réponse "answers" d’Azure Search (si dispo)
        if answers:
            best = answers[0]
            txt = (best.get("text") or "").strip()
            if txt:
                contexts.append(
                    {
                        "title": "Azure AI Search — Réponse",
                        "snippet": txt,
                        "meta": {"kind": "answer", "key": best.get("key"), "score": best.get("score")},
                    }
                )

        # Documents
        for d in hits[:top]:
            title = d.get("title") or d.get("path") or d.get("source_path") or "Document"
            caps = d.get("@search.captions") or []
            cap_text = caps[0].get("text") if caps else ""
            snippet = (cap_text if cap_text else (d.get("content") or ""))[:1000]
            contexts.append(
                {
                    "title": title,
                    "snippet": snippet,
                    "meta": {
                        "id": d.get("id"),
                        "path": d.get("path") or d.get("source_path"),
                        "score": d.get("@search.score"),
                        "reranker": d.get("@search.rerankerScore"),
                    },
                }
            )
        return contexts

    def handle(self, req):
        # Historique court
        hist = self._chat_history_block(req.claims, req.conversation_id)

        # top_k défensif
        try:
            top_k = int(getattr(req, "top_k", 4))
        except Exception:
            top_k = 4
        top_k = max(1, min(top_k, 8))

        contexts = self._contexts_from_search(req.question, getattr(req, "filters", None), top_k)

        if not contexts:
            return _result(
                "Je ne trouve pas d’information pertinente dans les documents fournis.",
                False,
                [],
                req,
            )

        # Construction du prompt (style "réponse JSON stricte" sans markdown)
        src_block: List[str] = []
        for i, c in enumerate(contexts, 1):
            title = c.get("title") or (c.get("meta", {}) or {}).get("path") or f"Source {i}"
            snippet = (c.get("snippet") or "")[:2000]
            src_block.append(f"[{i}] {title}\n{snippet}")

        user = (("HISTORIQUE:\n" + hist + "\n\n") if hist else "") + \
               f"QUESTION:\n{req.question}\n\nSOURCES:\n" + "\n\n".join(src_block)

        sys_rules = (
            "Tu es un assistant d’entreprise pour un système RAG. Réponds exclusivement aux SOURCES fournies. "
            'Sortie JSON stricte: {"answer":"...","uses_context":true|false,"used_sources":[<indices>]}. '
            "Pas de markdown ni d’emojis."
        )

        llm = get_llm(preferred=None)  # provider par défaut (llm.yaml / settings)
        try:
            obj = llm.generate_json(user, sys_rules, max_tokens=900, temperature=0.2)
        except Exception as e:
            # fallback minimal si l’appel LLM échoue
            return _result(f"Erreur de génération: {e}", False, [], req)

        answer = (obj.get("answer") or "").strip() or "Réponse vide."
        uses = bool(obj.get("uses_context", False))

        # Indices utilisés -> mapping vers docs
        used_idx_raw = obj.get("used_sources") or []
        used_idx: List[int] = []
        for x in used_idx_raw:
            try:
                used_idx.append(int(x))
            except Exception:
                continue

        docs: List[Dict[str, Any]] = []
        for i in used_idx:
            if 1 <= i <= len(contexts):
                c = contexts[i - 1]
                # ignorer l’item "answer" si présent
                if (c.get("meta", {}) or {}).get("kind") == "answer":
                    continue
                docs.append(
                    {
                        "id": (c.get("meta") or {}).get("id"),
                        "title": c.get("title"),
                        "path": (c.get("meta") or {}).get("path"),
                        "score": (c.get("meta") or {}).get("score"),
                        "reranker": (c.get("meta") or {}).get("reranker"),
                    }
                )

        if not docs and uses:
            # fallback: montrer les 3 premiers docs contextuels non-"answer"
            for c in [c for c in contexts if (c.get("meta", {}) or {}).get("kind") != "answer"][:3]:
                docs.append(
                    {
                        "id": (c.get("meta") or {}).get("id"),
                        "title": c.get("title"),
                        "path": (c.get("meta") or {}).get("path"),
                        "score": (c.get("meta") or {}).get("score"),
                        "reranker": (c.get("meta") or {}).get("reranker"),
                    }
                )

        return _result(answer, uses, docs, req)


def _result(answer: str, uses: bool, docs: List[Dict[str, Any]], req) -> dict:
    return {
        "answer": answer,
        "uses_context": uses,
        "used_docs": docs,
        "citations": [],  # citations inline gérées côté front si besoin
        "conversation_id": getattr(req, "conversation_id", None),
    }
