from fastapi import APIRouter

from .routes_health import router as health_router
from .routes_auth import router as auth_router
from .routes_chat import router as chat_router
from .routes_docs import router as docs_router

router = APIRouter()
router.include_router(health_router, prefix="", tags=["health"])
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(chat_router, prefix="/api", tags=["chat"])
router.include_router(docs_router, prefix="/api", tags=["docs"])
