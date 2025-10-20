"""
Sécurité (authentification/autorisation) pour l'orchestrateur.

Expose des dépendances FastAPI et utilitaires communs:
- require_user:   dépendance principale qui valide le JWT et le scope/role.
- verify_jwt:     vérifie et décode un token JWT signé par Entra ID.
- require_scope:  contrôle d'accès basé sur scopes/roles.
"""

from .auth import (
    require_user,
    verify_jwt,
    require_scope,
    get_current_user,
    ensure_auth_config,
    bearer_optional,
    bearer_required,
)
