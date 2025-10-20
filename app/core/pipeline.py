from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from app.retrieval import AzureSearch, in_scope, best_answers
from app.llm import get_llm
from app.core.typing import RagContextDoc, SynthConfig
from app.utils.text import clean_markdown


class RagPipeline:
    """
    Pipeline générique retrieve → rank → synthesize.

    Peut être utilisé par défaut pour le route 'rag' ou réutilisé dans des agents custom.
    """

    def __init__(self, index_name: str, query_type: str = "semantic"):
        self.index_name = index_name
        self.query_type = query_type
        self.client = AzureSearch()

    # -------------------- RETRIEVE --------------------

    def retrieve(
        self,
        query: str,
        *,
        filters: Optional[Dict[str, Any]],
        top: int,
        want_answers: bool = True,
        want_captions: bool = True,
        select: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self.client.search(
            index=self.index_name,
            query=query or "*",
            filters=filters,
            top=top,
            answers=want_answers,
            captions=want_captions,
            query_type=self.query_type,
            select=select,
        )

    # -------------------- BUILD CONTEXT --------------------

    def build_contexts_from_search(
        self,
        search_json: Dict[str, Any],
        top: int,
        include_answer_as_context: bool = True,
        snippet_len: int = 1000,
    ) -> List[RagContextDoc]:
        hits = search_json.get("value", []) or []
        ans = best_answers(search_json)

        ctx: List[RagContextDoc] = []

        # Answer context optionnel (non sourçable directement → meta.kind="answer")
        if include_answer_as_context and ans:
            best = ans[0]
            txt = (best.get("text") or "").strip()
            if txt:
                ctx.append(
                    RagContextDoc(
                        title="Azure AI Search — Réponse",
                        snippet=txt[:snippet_len],
                        meta={"kind": "answer", "key": best.get("key"), "score": best.get("score")},
                    )
                )

        # Top documents
        for d in hits[:top]:
            title = d.get("title") or d.get("path") or d.get("source_path") or "Document"
            caps = d.get("@search.captions") or []
            cap_text = caps[0].get("text") if caps else ""
            base = cap_text if cap_text else (d.get("content") or "")
            ctx.append(
                RagContextDoc(
                    title=title,
                    snippet=base[:snippet_len],
                    meta={
                        "id": d.get("id"),
                        "path": d.get("path") or d.get("source_path"),
                        "score": d.get("@search.score"),
                        "reranker": d.get("@search.rerankerScore"),
                    },
                )
            )

        return ctx

    # -------------------- SYNTHESIZE --------------------

    def synthesize_json(
        self,
        question: str,
        contexts: List[RagContextDoc],
        *,
        hist_block: str = "",
        synth: Optional[SynthConfig] = None,
    ) -> Tuple[str, bool, List[int]]:
        """
        Appelle le LLM en demandant un JSON strict:
        { "answer": "...", "uses_context": true|false, "used_sources": [<indices 1..N>] }
        """
        synth = synth or SynthConfig()
        llm = get_llm(synth.provider)

        # Construire SOURCES 1..N
        src_block: List[str] = []
        for i, c in enumerate(contexts, 1):
            title = c.title or (c.meta.get("path") if c.meta else f"Source {i}")
            snippet = (c.snippet or "")[:2000]
            src_block.append(f"[{i}] {title}\n{snippet}")

        # Historique + question + sources
        user = ((f"HISTORIQUE:\n{hist_block}\n\n") if hist_block else "") + \
               f"QUESTION:\n{question}\n\nSOURCES:\n" + "\n\n".join(src_block)

        sys_rules = synth.system_rules or (
            "Tu es un assistant d’entreprise pour un système RAG. "
            "Réponds STRICTEMENT aux SOURCES; si l’info n’y est pas: dis que tu ne la trouves pas. "
            ""
            "Sortie JSON stricte: {\"answer\":\"...\",\"uses_context\":true|false,\"used_sources\":[<indices>]}."
        )

        obj = llm.generate_json(
            user,
            sys_rules,
            max_tokens=int(synth.max_output_tokens),
            temperature=float(synth.temperature),
        )

        answer = (obj.get("answer") or "").strip() or "Réponse vide."
        uses = bool(obj.get("uses_context", False))
        used_idx = []
        for x in (obj.get("used_sources") or []):
            try:
                used_idx.append(int(x))
            except Exception:
                continue
        return answer, uses, used_idx

    # -------------------- CONVENIENCE ALL-IN-ONE --------------------

    def run(
        self,
        question: str,
        *,
        filters: Optional[Dict[str, Any]],
        top_k: int = 8,
        include_answer_as_context: bool = True,
        hist_block: str = "",
        synth: Optional[SynthConfig] = None,
    ) -> Dict[str, Any]:
        res = self.retrieve(
            question,
            filters=filters,
            top=top_k,
            want_answers=True,
            want_captions=True,
        )
        hits = res.get("value", []) or []
        if not in_scope(hits) and not best_answers(res):
            return {
                "answer": "Je ne trouve pas d’information pertinente dans les documents fournis.",
                "uses_context": False,
                "used_docs": [],
                "citations": [],
            }

        ctx = self.build_contexts_from_search(
            res, top=min(top_k, 8), include_answer_as_context=include_answer_as_context
        )
        answer, uses, used_idx = self.synthesize_json(
            question, ctx, hist_block=hist_block, synth=synth
        )

        # map used_docs (sauter meta.kind=answer)
        used_docs: List[Dict[str, Any]] = []
        for i in used_idx:
            if 1 <= i <= len(ctx):
                c = ctx[i - 1]
                if (c.meta or {}).get("kind") == "answer":
                    continue
                used_docs.append(
                    {
                        "id": (c.meta or {}).get("id"),
                        "title": c.title,
                        "path": (c.meta or {}).get("path"),
                        "score": (c.meta or {}).get("score"),
                        "reranker": (c.meta or {}).get("reranker"),
                    }
                )

        if not used_docs and uses:
            # fallback: 3 premiers docs non-answer
            for c in [c for c in ctx if (c.meta or {}).get("kind") != "answer"][:3]:
                used_docs.append(
                    {
                        "id": (c.meta or {}).get("id"),
                        "title": c.title,
                        "path": (c.meta or {}).get("path"),
                        "score": (c.meta or {}).get("score"),
                        "reranker": (c.meta or {}).get("reranker"),
                    }
                )

        return {
            "answer": answer,
            "uses_context": uses,
            "used_docs": used_docs,
            "citations": [],
        }
