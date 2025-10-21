# ARCHITECTURE

> Ce document décrit l’architecture du backend **AINA** (RAG entreprise + domaines Finance/Trading/RH). Il sert de guide pour comprendre les composants, les flux, les dépendances Azure et les conventions.

---

## 1) Vue d’ensemble

Le projet est une API **FastAPI** qui orchestre des **agents** spécialisés (RAG documents, tableurs, vision/OCR, trading, RH).

- **API** (`app/api/*`) : routes HTTP (santé, auth, chat, docs).
- **Core** (`app/core/*`) : orchestration (sélection d’agent, pipeline RAG).
- **LLM** (`app/llm/*`) : abstraction fournisseurs (Azure OpenAI, Gemini, DeepSeek).
- **Retrieval** (`app/retrieval/*`) : Azure AI Search + post-ranking.
- **Storage** (`app/storage/*`) : Azure Blob (sources), **Table Storage** (historique chat).
- **Sécurité** (`app/security/*`) : validation JWT Entra ID, scopes.
- **Config** (`app/config/*`) : YAML déclaratifs (indexes, LLM, CORS).
- **Utils** (`app/utils/*`) : helpers (texte, IDs, logging).

### Arborescence

