"""Authentication endpoints supporting OIDC Keycloak discovery and demo mode."""
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.config import settings
from app.core.security import (
    AuthUser,
    create_signed_token,
    generate_pkce_pair,
    get_current_user,
)
from app.models.schemas import DemoLoginRequest, TokenResponse, UserProfile

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.get("/config")
def get_auth_config() -> Dict[str, str]:
    """Provide OIDC discovery and Keycloak client configuration to SPA frontend."""
    return {
        "keycloak_url": settings.keycloak_url,
        "realm": settings.keycloak_realm,
        "client_id": settings.keycloak_client_id,
        "issuer": f"{settings.keycloak_url}/realms/{settings.keycloak_realm}",
        "demo_mode": str(settings.demo_mode).lower(),
        "environment": settings.environment,
    }


@router.get("/pkce-params")
def get_pkce_parameters() -> Dict[str, str]:
    """Generate ephemeral RFC 7636 PKCE code challenge and verifier."""
    return generate_pkce_pair()


@router.post("/demo-login", response_model=TokenResponse)
def demo_login(req: DemoLoginRequest) -> TokenResponse:
    """Acquire a local development Bearer token for testing roles (strictly forbidden in production)."""
    if not settings.demo_mode or settings.environment == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo login is disabled in this environment. Please authenticate via Keycloak OIDC.",
        )

    valid_roles = ["viewer", "analyst", "admin"]
    selected_role = req.role.lower()
    if selected_role not in valid_roles:
        selected_role = "viewer"

    username = req.username.strip() or f"demo-{selected_role}"
    user_id = f"demo-user-{selected_role}"

    # Standard OIDC token claims structure matching Keycloak realm roles
    token = create_signed_token({
        "sub": user_id,
        "preferred_username": username,
        "email": f"{username}@local.demo",
        "roles": [selected_role],
        "realm_access": {"roles": [selected_role]},
        "is_demo": True,
    })

    return TokenResponse(
        access_token=token,
        token_type="Bearer",
        expires_in=3600,
        roles=[selected_role],
        username=username,
        is_demo=True,
    )


@router.get("/me", response_model=UserProfile)
def get_current_user_profile(user: AuthUser = Depends(get_current_user)) -> UserProfile:
    """Return verified profile and role privileges for the active Bearer session."""
    return UserProfile(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        roles=user.roles,
        is_demo=user.is_demo,
    )
