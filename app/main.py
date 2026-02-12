from app.core.config import app, _parse_origins  # app FastAPI déjà créé + CORS
from app.core.security import _require_auth_config, jwt, JWKS_URL

# Routers
from app.routers.health import router as health_router
from app.routers.auth import router as auth_router
from app.routers.sas import router as sas_router
from app.routers.chat import router as chat_router
from app.routers.rag import router as rag_router
from app.routers.trading import router as trading_router
from app.routers.finance import router as finance_router
from app.routers.aina_finance import router as finance_aina_router
from app.routers.aina_trading_finance import router as trading_finance_router
from app.routers.trading_doc import router as trading_doc_router
from app.routers.trading_doc_sas import router as trading_doc_sas_router
from app.routers.websearch import router as websearch_router
from app.routers.vision import router as vision_router
from app.routers.vision_sas import router as vision_sas_router
from app.routers.vision_cleanup import router as vision_cleanup_router
from app.routers.vision_attach import router as vision_attach_router
from app.routers.vet_doc import router as vet_doc_router 
from app.routers.aina_vet_finance import router as vet_finance_aina_router
from app.routers.routes_email import router as email_router
from app.routers.routes_email_attachments import router as email_attachments_router


# Mount routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(sas_router)
app.include_router(chat_router)
app.include_router(rag_router)
app.include_router(trading_router)
app.include_router(finance_router)
app.include_router(websearch_router)
app.include_router(vision_router)
app.include_router(vision_sas_router)
app.include_router(vision_cleanup_router)
app.include_router(vision_attach_router)
app.include_router(finance_aina_router)
app.include_router(trading_finance_router)
app.include_router(trading_doc_router)
app.include_router(trading_doc_sas_router)
app.include_router(vet_doc_router)
app.include_router(vet_finance_aina_router)
app.include_router(email_router)
app.include_router(email_attachments_router)


# Startup checks (inchangés)
@app.on_event("startup")
def _startup_auth_check():
    _require_auth_config()
    if not JWKS_URL:
        raise RuntimeError("JWKS_URL not derived; verify TENANT_ID.")
    if jwt is None:
        raise RuntimeError("PyJWT not installed. Installe: pip install 'PyJWT[crypto]'")
