import os, datetime, urllib.parse, time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ====== Chargement dotenv facultatif ======
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# ====== Variables d’environnement / constantes ======
FRONT_ORIGIN = os.getenv("FRONT_ORIGIN", "*")
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX", "idx-rag-chunks")
AZURE_SEARCH_API_VER = os.getenv("AZURE_SEARCH_API_VERSION", "2023-11-01")
AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
AZURE_SEARCH_INDEX_FINANCE = os.getenv("AZURE_SEARCH_INDEX_FINANCE", "idx-finance-csv")
RETRIEVAL_K = int(os.getenv("RAG_RETRIEVAL_K", "50"))
TOPN_MAX = int(os.getenv("RAG_TOPN_MAX", "8"))
RERANKER_MIN = float(os.getenv("RAG_RERANKER_MIN", "1.2"))
BM25_MIN = float(os.getenv("RAG_BM25_MIN", "1.0"))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL_CHAT = os.getenv("GEMINI_MODEL_CHAT", "gemini-2.5-flash")
GEMINI_MAX_OUTPUT_TOKENS = int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "700"))
GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.2"))
GEMINI_RETRIES = int(os.getenv("GEMINI_RETRIES", "4"))
TENANT_ID = os.getenv("TENANT_ID", "").strip()
CLIENT_ID = os.getenv("CLIENT_ID", "").strip()
REQUIRED_SCOPE = os.getenv("REQUIRED_SCOPE", "").strip()
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
JWKS_URL = f"{AUTHORITY}/discovery/v2.0/keys"
ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT")
ACCOUNT_KEY  = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
CONTAINER    = os.getenv("AZURE_STORAGE_CONTAINER", "docs")
CONTAINER_TRADING = os.getenv("AZURE_STORAGE_CONTAINER_TRADING", "docs")
AZURE_SEARCH_INDEX_TRADING = os.getenv("AZURE_SEARCH_INDEX_TRADING", "idx-oil-demo")
GEMINI_MODEL_WEB = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
USE_GROUNDING = os.getenv("USE_GROUNDING", "1") == "1"
RAG_USE_VECTOR = os.getenv("RAG_USE_VECTOR", "1") == "1"
RAG_VECTOR_K   = int(os.getenv("RAG_VECTOR_K", "50"))
RAG_VECTOR_FIELDS = os.getenv("RAG_VECTOR_FIELDS", "content_vector")
RAG_SEM_CONFIG = os.getenv("RAG_SEM_CONFIG", "sem-default")
AOAI_ENDPOINT = os.getenv("AOAI_ENDPOINT", "").rstrip("/")
AOAI_API_KEY = os.getenv("AOAI_API_KEY", "")
AOAI_EMBED_DEPLOYMENT = os.getenv("AOAI_EMBED_DEPLOYMENT", "text-embedding-3-large")
AOAI_API_VERSION = os.getenv("AOAI_API_VERSION", "2024-08-01-preview")
RAG_VECTOR_INTEGRATED = os.getenv("RAG_VECTOR_INTEGRATED", "0") == "1"
CHAT_HISTORY_TURNS=6
CHAT_HISTORY_CHARS=5500
CLARIFY_MAX_TURNS = int(os.getenv("CLARIFY_MAX_TURNS", "2"))
CLARIFY_SCORE_SLACK = float(os.getenv("CLARIFY_SCORE_SLACK", "0.15"))
CHAT_TABLE = os.getenv("AZURE_TABLE_CHAT", "chatmessages")
import os

# ≡≡≡ Azure Table Storage / Chat history ≡≡≡
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "").strip()
ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT", "").strip()
ACCOUNT_KEY  = os.getenv("AZURE_STORAGE_ACCOUNT_KEY", "").strip()

CHAT_TABLE   = os.getenv("AZURE_TABLE_CHAT", "chatmessages")
CHAT_BACKEND = os.getenv("CHAT_BACKEND", "table").lower()  # "table" | "memory"

# (optionnel) sécurité / auth si tu en as besoin ailleurs
TENANT_ID = os.getenv("TENANT_ID", "").strip()
CLIENT_ID = os.getenv("CLIENT_ID", "").strip()
REQUIRED_SCOPE = os.getenv("REQUIRED_SCOPE", "").strip()

# === Aina Vision config ===
AZURE_OAI_ENDPOINT = os.environ.get("AZURE_OAI_ENDPOINT", "")
AZURE_OAI_KEY = os.environ.get("AZURE_OAI_KEY", "")
AZURE_OAI_DEPLOYMENT = os.environ.get("AZURE_OAI_DEPLOYMENT", "o3-mini")

CV_ENDPOINT = os.environ.get("CV_ENDPOINT", "")
CV_PRED_KEY = os.environ.get("CV_PRED_KEY", "")
CV_PROJECT_ID = os.environ.get("CV_PROJECT_ID", "")
CV_PUBLISHED_NAME = os.environ.get("CV_PUBLISHED_NAME", "")
CV_MIN_CONFIDENCE = float(os.environ.get("CV_MIN_CONFIDENCE", 0.6))



# === Plaque OCR / GPT ===
PLAQUE_AZURE_OCR_ENDPOINT = os.getenv("PLAQUE_AZURE_OCR_ENDPOINT", "").strip()
PLAQUE_AZURE_OCR_KEY = os.getenv("PLAQUE_AZURE_OCR_KEY", "").strip()
PLAQUE_AZURE_OCR_MODEL_ID = os.getenv("PLAQUE_AZURE_OCR_MODEL_ID", "prebuilt-read").strip()

PLAQUE_AZURE_OAI_ENDPOINT = os.getenv("PLAQUE_AZURE_OAI_ENDPOINT", AZURE_OAI_ENDPOINT).strip()
PLAQUE_AZURE_OAI_KEY = os.getenv("PLAQUE_AZURE_OAI_KEY", AZURE_OAI_KEY).strip()
PLAQUE_AZURE_OAI_DEPLOYMENT = os.getenv("PLAQUE_AZURE_OAI_DEPLOYMENT", AZURE_OAI_DEPLOYMENT).strip()
PLAQUE_AZURE_OAI_API_VERSION = os.getenv("PLAQUE_AZURE_OAI_API_VERSION", "2024-07-01-preview").strip()

PLAQUE_METADATA_FILE = os.getenv("PLAQUE_METADATA_FILE", "Resultats/metadata.csv")

PLAQUE_TENANT_ID = os.getenv("PLAQUE_TENANT_ID", TENANT_ID).strip()
PLAQUE_CLIENT_ID = os.getenv("PLAQUE_CLIENT_ID", "").strip()
PLAQUE_CLIENT_SECRET = os.getenv("PLAQUE_CLIENT_SECRET", "").strip()
PLAQUE_SHAREPOINT_DOMAIN = os.getenv("PLAQUE_SHAREPOINT_DOMAIN", "").strip()
PLAQUE_SHAREPOINT_SITE_PATH = os.getenv("PLAQUE_SHAREPOINT_SITE_PATH", "").strip()
PLAQUE_SHAREPOINT_DRIVE_NAME = os.getenv("PLAQUE_SHAREPOINT_DRIVE_NAME", "Documents").strip()

PLAQUE_CLIENT_NAME = os.getenv("PLAQUE_CLIENT_NAME", "Cultura")


MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY", "")

# Modèle Kimi utilisé pour RAG "single fiche" (synthèse RAG classique)
KIMI_MODEL_SINGLE = os.getenv("KIMI_MODEL_SINGLE", "kimi-k2-turbo-preview")

# Modèle Kimi utilisé pour le cas "global PDF"
KIMI_MODEL_GLOBAL = os.getenv("KIMI_MODEL_GLOBAL", "kimi-k2-turbo-preview")

# PDF global (toutes fiches d’audit) stocké sur Azure Blob
GLOBAL_AUDIT_CONTAINER = os.getenv("GLOBAL_AUDIT_CONTAINER", "audit-global")
GLOBAL_AUDIT_BLOB_PATH = os.getenv(
    "GLOBAL_AUDIT_BLOB_PATH", 
    "all_fiches_audit.pdf"  # le blob path dans le container
)

# Aïna Finance
FINANCE_CONTAINER = os.getenv("FINANCE_CONTAINER", "audit-global")
FINANCE_BLOB_PATH = os.getenv("FINANCE_BLOB_PATH", "audit-magasin.xlsx")

VET_INDEX_NAME: str = os.getenv("VET_INDEX_NAME", "vet-knowledge-index")
VET_RETRIEVAL_K: int = int(os.getenv("VET_RETRIEVAL_K", "5"))
# Si tu as déjà KIMI_MODEL_SINGLE, on peut s’en servir comme fallback
KIMI_MODEL_VET_DOC: str = os.getenv("KIMI_MODEL_VET_DOC", KIMI_MODEL_SINGLE)


# Aïna Vet Finance
VET_FINANCE_CONTAINER = os.getenv("VET_FINANCE_CONTAINER", "vet-finance")
VET_FINANCE_BLOB_PATH = os.getenv("VET_FINANCE_BLOB_PATH", "vet_finance.ods")

# Container pour les images d'audit
AUDIT_IMAGE_CONTAINER = os.getenv("AUDIT_IMAGE_CONTAINER", "auditimage")
# === CORS util ===
def _parse_origins(env_value: str) -> list[str]:
    if not env_value:
        return []
    return [o.strip() for o in env_value.split(",") if o.strip()]

DEFAULT_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://app-rag-climmag-prod.azurewebsites.net",
    "https://st4x2hamb3rger.z28.web.core.windows.net",
    "https://stitsynchrag12732.z28.web.core.windows.net",
]
origins = _parse_origins(os.getenv("FRONT_ORIGIN", "")) or DEFAULT_ORIGINS

app = FastAPI(title="RAG Enterprise + Aina Finance (Gemini)", version="1.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)
