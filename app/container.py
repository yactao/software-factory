from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router as api_router
from app.settings import get_settings


def build_app() -> FastAPI:
    s = get_settings()

    app = FastAPI(
        title=s.app_name,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS (origins depuis FRONT_ORIGIN CSV ou defaults)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=s.cors_allow_origins or ["*"],
        allow_credentials=s.cors_allow_credentials,
        allow_methods=s.cors_allow_methods or ["*"],
        allow_headers=s.cors_allow_headers or ["*"],
        expose_headers=s.cors_expose_headers or ["*"],
    )

    # Routers (health, auth, chat, docs)
    app.include_router(api_router)

    # Startup checks légers (optionnels)
    @app.on_event("startup")
    async def _startup():
        # Ici tu peux ajouter des checks rapides: env requis, etc.
        # On reste léger pour ne pas empêcher le démarrage si un service est temporairement KO.
        pass

    return app
