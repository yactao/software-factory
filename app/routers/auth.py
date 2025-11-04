# app/routers/auth.py
from fastapi import APIRouter, Depends
from ..core.security import _auth_dependency, _require_scope, get_current_user

router = APIRouter()

@router.get("/auth/debug")
def auth_debug(claims: dict = Depends(_auth_dependency)):
    _require_scope(claims)
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
def secure_route(user: dict = Depends(get_current_user)):
    return {"message": "✅ Accès autorisé", "user": user}
