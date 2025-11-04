# app/core/security.py
import requests, re
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .config import TENANT_ID, CLIENT_ID, JWKS_URL, REQUIRED_SCOPE
# ====== COLLE ICI SANS MODIFIER: import jwt / PyJWKClient et helpers ======
try:
    import jwt
    from jwt import PyJWKClient
except Exception:
    jwt = None
    PyJWKClient = None

bearer_schema = HTTPBearer(auto_error=False)
bearer_scheme = HTTPBearer()

def _require_auth_config():
    if not TENANT_ID or not CLIENT_ID:
        raise HTTPException(500, "Auth not configured. Check TENANT_ID and CLIENT_ID in .env.")

# Charger JWKS au démarrage (copie inchangée)
try:
    resp = requests.get(JWKS_URL, timeout=10)
    resp.raise_for_status()
    jwks = resp.json()
    if "keys" not in jwks:
        raise RuntimeError("JWKS invalide, 'keys' manquant")
except Exception as e:
    raise RuntimeError(f"Impossible de charger JWKS depuis {JWKS_URL}: {e}")

def _verify_jwt(token: str) -> dict:
    try:
        jwks_client = PyJWKClient(JWKS_URL)
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=f"api://{CLIENT_ID}",
            options={"verify_aud": False, "verify_exp": False}
        )
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token invalide: {str(e)}")

def _auth_dependency(credentials: HTTPAuthorizationCredentials = Depends(bearer_schema)) -> dict:
    if not credentials or not credentials.credentials:
        raise HTTPException(401, "Authorization manquante (Bearer token)")
    return _verify_jwt(credentials.credentials)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    return _verify_jwt(credentials.credentials)

def _require_scope(claims: dict, required: str = REQUIRED_SCOPE):
    if not required:
        return
    required_set = {s.strip() for s in required.split(",") if s.strip()}
    scp = {s.strip() for s in str(claims.get("scp", "")).split() if s.strip()}
    if scp & required_set:
        return
    roles_claim = claims.get("roles", [])
    if isinstance(roles_claim, str):
        roles = {r.strip() for r in roles_claim.split() if r.strip()}
    else:
        roles = {str(r).strip() for r in roles_claim if str(r).strip()}
    if roles & required_set:
        return
    raise HTTPException(403, f"Scope or role {required} required.")
