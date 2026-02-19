# Trading Doc Route — Integration

New endpoint: **POST /api/trading/doc** (RAG over trading documents index, semantic search, Kimi synthesis).

## New files (no existing files modified)

- `app/services/search_azure_trading_doc.py` — Azure Search over index `aina-trading-docs-idx` (or `AZURE_SEARCH_INDEX_TRADING_DOC`)
- `app/services/kimi_trading_doc_rag.py` — Synthesis with Kimi via `llm_chat_completion("rag_single", ...)`
- `app/routers/trading_doc.py` — Router with auth, smalltalk, language detection, chat history

## Register the router (manual step)

In **`app/main.py`**:

1. Add the import (with the other router imports):

```python
from app.routers.trading_doc import router as trading_doc_router
```

2. Include the router (with the other `app.include_router(...)` calls):

```python
app.include_router(trading_doc_router)
```

No other changes to existing code are required.

## Environment (optional)

- **`AZURE_SEARCH_INDEX_TRADING_DOC`** — Index name; default: `aina-trading-docs-idx`
- Index must have a **semantic configuration** named **`semantic-config`** (as in the search payload).
- Auth and search use existing config: `AZURE_SEARCH_ENDPOINT`, `AZURE_SEARCH_API_KEY`, `REQUIRED_SCOPE`, etc.
- LLM uses existing RAG Kimi config (`RAG_LLM_PROVIDER`, `RAG_MODEL_SINGLE`, etc.).

## Response shape (same as /api/rag for frontend)

```json
{
  "answer": "string",
  "citations": [],
  "used_docs": [{ "title": "...", "path": "...", "snippet": "...", "score": ..., "meta": { "chunk_index": ..., "section": ..., "score": ... } }],
  "conversation_id": "string",
  "model": "Aïna Instant"
}
```

Images are not included (documents only).
