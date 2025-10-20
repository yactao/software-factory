# app/settings.py
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import List, Optional


# ---------- helpers ----------
def _getenv(name: str, default: Optional[str] = None) -> Optional[str]:
    v = os.getenv(name)
    if v is None:
        return default
    v = str(v).strip()
    return v if v != "" else default


def _split_csv(v: Optional[str]) -> List[str]:
    if not v:
        return []
    return [s.strip() for s in v.split(",") if s.strip()]


@dataclass
class Settings:
    # ===== App / Logs =====
    app_name: str = _getenv("APP_NAME", "RAG Enterprise + Aina Finance")
    log_level: str = _getenv("LOG_LEVEL", "info")
    debug_json: bool = bool(int(_getenv("DEBUG_JSON", "0")))

    # ===== CORS =====
    front_origin_csv: str = _getenv(
        "FRONT_ORIGIN",
        "http://localhost:5173,http://127.0.0.1:5173,https://app-rag-climmag-prod.azurewebsites.net",
    )
    cors_allow_origins: List[str] = None  # filled in __post_init__
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = None
    cors_allow_headers: List[str] = None
    cors_expose_headers: List[str] = None

    # ===== Azure AI Search =====
    search_endpoint: Optional[str] = _getenv("AZURE_SEARCH_ENDPOINT") or _getenv("SEARCH_ENDPOINT")
    search_api_version: str = _getenv("AZURE_SEARCH_API_VERSION", _getenv("SEARCH_API_VERSION", "2023-11-01"))
    search_api_key: Optional[str] = _getenv("AZURE_SEARCH_API_KEY") or _getenv("SEARCH_API_KEY")

    # Index (alignés avec /config/indexes/*.yaml)
    index_chunks: str = _getenv("AZURE_SEARCH_INDEX", _getenv("SEARCH_INDEX", "idx-rag-chunks"))
    index_finance: str = _getenv("AZURE_SEARCH_INDEX_FINANCE", "idx-finance-csv")
    index_trading: str = _getenv("AZURE_SEARCH_INDEX_TRADING", "idx-oil-demo")
    index_hr: str = _getenv("AZURE_SEARCH_INDEX_HR", "idx-hr")

    # RAG thresholds/limits
    rag_retrieval_k: int = int(_getenv("RAG_RETRIEVAL_K", "50"))
    rag_topn_max: int = int(_getenv("RAG_TOPN_MAX", "8"))
    rag_reranker_min: float = float(_getenv("RAG_RERANKER_MIN", "1.2"))
    rag_bm25_min: float = float(_getenv("RAG_BM25_MIN", "1.0"))

    # ===== Azure OpenAI (optionnel) =====
    azure_openai_endpoint: Optional[str] = _getenv("AZURE_OPENAI_ENDPOINT")
    azure_openai_deployment: Optional[str] = _getenv("AZURE_OPENAI_DEPLOYMENT") or _getenv(
        "AZURE_OPENAI_DEPLOYMENT_CHAT"
    )
    azure_openai_api_version: str = _getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
    openai_api_key: Optional[str] = _getenv("AZURE_OPENAI_API_KEY") or _getenv("AZURE_OPENAI_KEY")
    aoai_connect_timeout: float = float(_getenv("AOAI_CONNECT_TIMEOUT", "0.8"))
    aoai_read_timeout: float = float(_getenv("AOAI_READ_TIMEOUT", "3.8"))
    request_deadline_seconds: float = float(_getenv("REQUEST_DEADLINE_SECONDS", "5.0"))
    aoai_use_msi: bool = bool(int(_getenv("AOAI_USE_MSI", "0")))  # 0/1

    # ===== Gemini / DeepSeek (optionnels) =====
    gemini_api_key: Optional[str] = _getenv("GEMINI_API_KEY")
    llm_provider: str = _getenv("LLM_PROVIDER", "gemini")  # gemini | openai | deepseek
    llm_model: Optional[str] = _getenv("LLM_MODEL", _getenv("GEMINI_MODEL_CHAT"))
    deepseek_api_key: Optional[str] = _getenv("DEEPSEEK_API_KEY")

    # Génération (paramètres par défaut – utilisés par les clients LLM)
    llm_temperature: float = float(_getenv("GEMINI_TEMPERATURE", "0.2"))
    llm_max_output_tokens: int = int(_getenv("GEMINI_MAX_OUTPUT_TOKENS", "900"))
    llm_retries: int = int(_getenv("GEMINI_RETRIES", "4"))

    # ===== Storage (Blob / Tables) =====
    storage_account: Optional[str] = _getenv("AZURE_STORAGE_ACCOUNT")
    storage_key: Optional[str] = _getenv("AZURE_STORAGE_ACCOUNT_KEY") or _getenv("AZURE_STORAGE_KEY")
    storage_conn_str: Optional[str] = _getenv("AZURE_STORAGE_CONNECTION_STRING")
    storage_container: str = _getenv("AZURE_STORAGE_CONTAINER", "docs")
    storage_container_trading: str = _getenv("AZURE_STORAGE_CONTAINER_TRADING", "docs")
    table_chat: str = _getenv("AZURE_TABLE_CHAT", "chatmessages")

    # ===== Auth (Entra ID / JWT) =====
    tenant_id: Optional[str] = _getenv("TENANT_ID")
    client_id: Optional[str] = _getenv("CLIENT_ID")  # = App Registration de l'API (resource) côté backend
    required_scope: str = _getenv("REQUIRED_SCOPE", "")  # ex: ragapi
    scope_uri: Optional[str] = _getenv("SCOPE_URI")  # ex: api://<API_CLIENT_ID>/ragapi (facultatif)
    authority: Optional[str] = None  # filled in __post_init__
    jwks_url: Optional[str] = None   # filled in __post_init__

    def __post_init__(self):
        # CORS
        self.cors_allow_origins = _split_csv(self.front_origin_csv)
        self.cors_allow_methods = ["*"]
        self.cors_allow_headers = ["*"]
        self.cors_expose_headers = ["*"]

        # Auth
        if self.tenant_id:
            self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
            self.jwks_url = f"{self.authority}/discovery/v2.0/keys"

    # ===== Aliases / Rétro-compat =====

    # storage.tables attend "storage_conn" → alias vers la connection string
    @property
    def storage_conn(self) -> Optional[str]:
        return self.storage_conn_str

    # certains modules lisent "azure_table_chat"
    @property
    def azure_table_chat(self) -> str:
        return self.table_chat

    # Certains bouts de code peuvent s'attendre à des noms AOAI "classiques"
    @property
    def aoai_endpoint(self) -> Optional[str]:
        return self.azure_openai_endpoint

    @property
    def aoai_api_version(self) -> Optional[str]:
        return self.azure_openai_api_version

    @property
    def aoai_deploy_chat(self) -> Optional[str]:
        return self.azure_openai_deployment

    @property
    def aoai_key(self) -> Optional[str]:
        return self.openai_api_key

    # Audience(s) acceptées pour la vérif JWT (utile si tu veux supporter 2 URI pendant une migration)
    @property
    def expected_audiences(self) -> List[str]:
        auds: List[str] = []
        if self.client_id:
            auds.append(f"api://{self.client_id}")
        if self.scope_uri:
            # ex: api://53897d93-.../ragapi -> base audience = api://53897d93-...
            base = self.scope_uri.rsplit("/", 1)[0] if "/" in self.scope_uri else self.scope_uri
            if base and base not in auds:
                auds.append(base)
        return auds

    @property
    def has_table_storage(self) -> bool:
        return bool(self.storage_conn_str or (self.storage_account and self.storage_key))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    s = Settings()
    s.__post_init__()  # dataclass manual post-init
    return s
