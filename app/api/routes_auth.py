from __future__ import annotations

from fastapi import APIRouter, Depends
from app.security.auth import require_user, require_scope

router = APIRouter()


@router.get("/debug")
def auth_debug(claims=Depends(require_user)):
    # Renvoie les claims utiles (sans le token brut)
    return {
        "message": "Token valid",
        "user": {
            "sub": claims.get("sub"),
            "name": claims.get("name"),
            "preferred_username": claims.get("preferred_username"),
        },
        "tenant": {"tid": claims.get("tid")},
        "token": {
            "iss": claims.get("iss"),
            "aud": claims.get("aud"),
            "scp": claims.get("scp"),
            "roles": claims.get("roles", []),
            "iat": claims.get("iat"),
            "exp": claims.get("exp"),
        },
    }


@router.get("/secure")
def secure_route(user=Depends(require_user)):
    # Exemple d’endpoint protégé
    return {"message": "✅ Accès autorisé", "user": user}
