import os
from typing import Optional

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

# Environment variables (same as frontend uses)
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "")

# Disable SSL verification for localhost, enable for production
SSL_VERIFY = "localhost" not in KEYCLOAK_URL

# Security scheme
security = HTTPBearer()

# Cache for JWKS
_jwks_cache: Optional[dict] = None


def get_jwks_url() -> str:
    """Build the JWKS URL from Keycloak configuration."""
    if not KEYCLOAK_URL or not KEYCLOAK_REALM:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Keycloak not configured",
        )
    return f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs"


def get_issuer() -> str:
    """Get the expected token issuer."""
    return f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}"


async def get_jwks() -> dict:
    """Fetch and cache JWKS from Keycloak."""
    global _jwks_cache
    if _jwks_cache is None:
        async with httpx.AsyncClient(verify=SSL_VERIFY) as client:
            response = await client.get(get_jwks_url())
            response.raise_for_status()
            _jwks_cache = response.json()
    return _jwks_cache


def get_signing_key(token: str, jwks: dict) -> dict:
    """Get the signing key for the token from JWKS."""
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")

    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unable to find signing key",
    )


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Verify JWT token and return the decoded payload."""
    token = credentials.credentials

    try:
        jwks = await get_jwks()
        signing_key = get_signing_key(token, jwks)

        payload = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            issuer=get_issuer(),
            options={"verify_aud": False},  # Audience varies by client
        )
        return payload

    except HTTPException:
        raise
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not verify token: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}",
        )


class User:
    """Parsed user information from token."""

    def __init__(self, payload: dict):
        self.sub = payload.get("sub")
        self.username = payload.get("preferred_username")
        self.email = payload.get("email")
        self.name = payload.get("name")
        self.roles = payload.get("realm_access", {}).get("roles", [])
        self.payload = payload


async def get_current_user(payload: dict = Depends(verify_token)) -> User:
    """Get the current authenticated user."""
    return User(payload)
