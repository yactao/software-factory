from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Dict, Iterable, Set

import requests
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# PyJWT avec support JWKS
try:
    import jwt
    from jwt import PyJWKClient
except Exception as e:  # pragma: no cover
    jwt = None
    PyJWKClient = None

from app.settings import get_settings

# ---------------------------------------------------------------------------
# Configuration de base et helpers
# ---------------------------------------------------------------------------

def ensure_auth_config() -> None:
    """Vérifie que les variables essentielles sont présentes."""
    s = get_settings()
    if not s.tenant_id or not s.client_id:
        raise HTTPException(
            status_code=500,
            detail="Auth non configurée: TENANT_ID ou CLIENT_ID manquant(s).",
        )


@lru_cache
def _jwks_url() -> str:
    s = get_settings()
    return f"https://login.microsoftonline.com/{s.tenant_id}/discovery/v2.0/keys"


@lru_cache
def _jwks_client() -> PyJWKClient:
    if jwt is None or PyJWKClient is None:  # pragma: no cover
        raise HTTPException(
            status_code=500,
            detail="PyJWT non installé. Installez 'PyJWT[crypto]'.",
        )
    return PyJWKClient(_jwks_url())


def _audience_value() -> str | None:
    """
    Valeur d'audience attendue. Beaucoup d’API AAD utilisent 'api://<client-id>'.
    Laisse None si tu veux désactiver la vérification d’audience via settings.
    """
    s = get_settings()
    # Autorise la désactivation via variable d'env AUDIENCE_DISABLED=true
    if os.getenv("AUTH_VERIFY_AUD", "true").lower() in ("0", "false", "no", "off"):
        return None
    return f"api://{s.client_id}"


# ---------------------------------------------------------------------------
# Vérification de jeton
# ---------------------------------------------------------------------------

def verify_jwt(token: str) -> Dict[str, Any]:
    """
    Décode et valide le JWT signé par Entra ID.
    - Algorithme: RS256 (JWKS)
    - Vérifie l'expiration.
    - Vérifie l'audience sauf si AUTH_VERIFY_AUD=false.
    """
    ensure_auth_config()

    try:
        signing_key = _jwks_client().get_signing_key_from_jwt(token)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Clé de signature introuvable: {e}")

    opts: Dict[str, Any] = {"verify_exp": True}
    aud = _audience_value()
    if aud is None:
        # Permettre des scénarios où l'audience est gérée par le gateway en amont
        opts["verify_aud"] = False
        aud = ""  # valeur neutre, non utilisée
    else:
        opts["verify_aud"] = True

    try:
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=aud,
            options=opts,
        )
        # Normalisation légère de types/présence
        if "scp" in payload and isinstance(payload["scp"], str):
            payload["scp"] = payload["scp"].strip()
        if "roles" in payload and isinstance(payload["roles"], list):
            payload["roles"] = [str(r) for r in payload["roles"]]
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expiré.")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token invalide: {e}")


# ---------------------------------------------------------------------------
# Contrôle d’accès (scopes/roles)
# ---------------------------------------------------------------------------

def _parse_claim_set(claim_value: Any) -> Set[str]:
    if not claim_value:
        return set()
    if isinstance(claim_value, str):
        # AAD place les scopes dans 'scp' sous forme "read write x"
        return {s for s in claim_value.split() if s}
    if isinstance(claim_value, Iterable):
        return {str(x) for x in claim_value if str(x)}
    return set()


def require_scope(claims: Dict[str, Any], required: str | None = None) -> None:
    """
    Vérifie que l'utilisateur possède au moins un des scopes/roles requis.
    - `required`: chaîne CSV (ex: "api.read,api.write") ; si None, lit settings.required_scope.
    """
    s = get_settings()
    required_csv = (required or s.required_scope or "").strip()
    if not required_csv:
        return  # aucun scope requis

    need: Set[str] = {x.strip() for x in required_csv.split(",") if x.strip()}
    if not need:
        return

    scopes = _parse_claim_set(claims.get("scp"))
    roles = _parse_claim_set(claims.get("roles"))

    if scopes.intersection(need) or roles.intersection(need):
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Accès refusé: nécessite l’un des scopes/roles {sorted(need)}.",
    )


# ---------------------------------------------------------------------------
# Dépendances FastAPI
# ---------------------------------------------------------------------------

# Schémas HTTP Bearer
bearer_optional = HTTPBearer(auto_error=False)
bearer_required = HTTPBearer(auto_error=True)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_required),
) -> Dict[str, Any]:
    """
    Dépendance simple: retourne les claims décodés (401 si invalide).
    N’impose pas de scope: pour les routes publiques protégées seulement par login.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Authorization manquante.")
    return verify_jwt(credentials.credentials)


def require_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_required),
) -> Dict[str, Any]:
    """
    Dépendance standard des routes API internes:
    - Valide le JWT
    - Valide les scopes/roles selon settings.REQUIRED_SCOPE (ou override par route)
    """
    claims = get_current_user(credentials)
    require_scope(claims)  # lit REQUIRED_SCOPE par défaut
    return claims
