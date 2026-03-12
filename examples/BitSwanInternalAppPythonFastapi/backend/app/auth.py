import os
import logging

import httpx
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.requests import Request

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)

KEYCLOAK_ISSUER_URL = os.environ.get("KEYCLOAK_ISSUER_URL")
if not KEYCLOAK_ISSUER_URL:
    raise RuntimeError("KEYCLOAK_ISSUER_URL is not set — cannot validate tokens")
JWKS_URL = f"{KEYCLOAK_ISSUER_URL}/protocol/openid-connect/certs"
_jwks_keys: list[dict] | None = None


async def _get_jwks_keys() -> list[dict]:
    """Fetch and cache JWKS public keys from Keycloak."""
    global _jwks_keys
    if _jwks_keys is not None:
        return _jwks_keys

    async with httpx.AsyncClient(verify=False) as client:
        resp = await client.get(JWKS_URL)
        resp.raise_for_status()
        _jwks_keys = resp.json().get("keys", [])
    return _jwks_keys


async def validate_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    """Validate a Bearer JWT token against Keycloak's JWKS keys."""

    if not credentials:
        raise HTTPException(status_code=401, detail="Missing authorization token")

    token = credentials.credentials
    try:
        keys = await _get_jwks_keys()
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")

        key_data = next((k for k in keys if k.get("kid") == kid), None)
        if not key_data:
            global _jwks_keys
            _jwks_keys = None
            keys = await _get_jwks_keys()
            key_data = next((k for k in keys if k.get("kid") == kid), None)
            if not key_data:
                raise HTTPException(status_code=401, detail="Unknown signing key")

        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key_data)
        payload = jwt.decode(
            token,
            key=public_key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


async def require_auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    """Router-level dependency that validates the token and stores claims on request.state."""
    claims = await validate_token(credentials)
    request.state.claims = claims


def get_username(claims: dict) -> str:
    return claims.get("preferred_username", "anonymous")


def get_username_from_request(request: Request) -> str:
    return get_username(request.state.claims)
