"""OIDC Bearer authentication and role-based access control."""
import base64
import hashlib
import os
import re
import time
from typing import Any, Dict, List, Optional
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from app.core.config import settings

bearer_scheme = HTTPBearer(auto_error=False)


class AuthUser(BaseModel):
    """Authenticated user profile with verified roles."""
    user_id: str
    username: str
    email: Optional[str] = None
    roles: List[str] = []
    is_demo: bool = False

    def has_any_role(self, required_roles: List[str]) -> bool:
        if "admin" in self.roles:
            return True
        return any(role in self.roles for role in required_roles)


def generate_pkce_pair() -> Dict[str, str]:
    """Generate RFC 7636 code verifier and S256 code challenge."""
    verifier = base64.urlsafe_b64encode(os.urandom(32)).decode("utf-8").rstrip("=")
    challenge_bytes = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(challenge_bytes).decode("utf-8").rstrip("=")
    return {"code_verifier": verifier, "code_challenge": challenge, "method": "S256"}


def verify_pkce(code_verifier: str, code_challenge: str) -> bool:
    """Verify S256 PKCE challenge against verifier."""
    if not code_verifier or not code_challenge:
        return False
    challenge_bytes = hashlib.sha256(code_verifier.encode("ascii")).digest()
    expected = base64.urlsafe_b64encode(challenge_bytes).decode("utf-8").rstrip("=")
    return expected == code_challenge


def create_signed_token(payload: Dict[str, Any], expires_in: int = 3600) -> str:
    """Create a signed JWT token using configured secret/key."""
    now = int(time.time())
    to_encode = payload.copy()
    to_encode.update({
        "iat": now,
        "exp": now + expires_in,
        "iss": f"{settings.keycloak_url}/realms/{settings.keycloak_realm}",
        "aud": settings.keycloak_client_id,
    })
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm="HS256")


def sanitize_token(token: str) -> str:
    """Return redacted representation of token for safe diagnostics without credential leak."""
    if not token or len(token) < 10:
        return "[REDACTED]"
    return f"{token[:4]}...{token[-4:]}"


def decode_and_validate_token(token: str) -> Dict[str, Any]:
    """Validate Bearer JWT claims against signature, issuer, and audience."""
    try:
        claims = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=["HS256"],
            audience=settings.keycloak_client_id,
            issuer=f"{settings.keycloak_url}/realms/{settings.keycloak_realm}",
            options={"verify_signature": True, "verify_aud": True, "verify_iss": True},
        )
        return claims
    except JWTError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(err)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> AuthUser:
    """Authenticate incoming request via Bearer token."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    claims = decode_and_validate_token(credentials.credentials)
    user_id = claims.get("sub", "unknown")
    username = claims.get("preferred_username", claims.get("name", user_id))
    email = claims.get("email")

    # Extract roles from standard OIDC Keycloak realm_access structure
    roles: List[str] = []
    if "realm_access" in claims and isinstance(claims["realm_access"], dict):
        roles.extend(claims["realm_access"].get("roles", []))
    if "roles" in claims and isinstance(claims["roles"], list):
        roles.extend(claims["roles"])

    normalized_roles = list(set(roles))
    is_demo = bool(claims.get("is_demo", False))

    return AuthUser(
        user_id=user_id,
        username=username,
        email=email,
        roles=normalized_roles,
        is_demo=is_demo,
    )


def require_roles(allowed_roles: List[str]):
    """Role-based authorization dependency guard."""
    async def role_checker(current_user: AuthUser = Depends(get_current_user)) -> AuthUser:
        if not current_user.has_any_role(allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {allowed_roles}. Current roles: {current_user.roles}",
            )
        return current_user

    return role_checker
