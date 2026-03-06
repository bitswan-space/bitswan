import os
import logging

import httpx
import jwt
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)
app = FastAPI()
security = HTTPBearer(auto_error=False)

# --- JWKS token validation ---

JWKS_URL = os.environ.get("OAUTH2_PROXY_OIDC_JWKS_URL")
_jwks_keys: list[dict] | None = None


async def _get_jwks_keys() -> list[dict]:
    """Fetch and cache JWKS public keys from Keycloak."""
    global _jwks_keys
    if _jwks_keys is not None:
        return _jwks_keys

    if not JWKS_URL:
        logger.warning("OAUTH2_PROXY_OIDC_JWKS_URL not set, token validation disabled")
        return []

    async with httpx.AsyncClient(verify=False) as client:
        resp = await client.get(JWKS_URL)
        resp.raise_for_status()
        _jwks_keys = resp.json().get("keys", [])
    return _jwks_keys


async def validate_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    """Validate a Bearer JWT token against Keycloak's JWKS keys."""
    if not JWKS_URL:
        # No JWKS configured — allow unauthenticated access (dev mode)
        return {}

    if not credentials:
        raise HTTPException(status_code=401, detail="Missing authorization token")

    token = credentials.credentials
    try:
        keys = await _get_jwks_keys()
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")

        key_data = next((k for k in keys if k.get("kid") == kid), None)
        if not key_data:
            # Key not found — JWKS may have rotated, refetch once
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


# --- CORS ---


def get_frontend_url() -> str | None:
    """Build frontend URL from BitSwan environment variables."""
    workspace = os.environ.get("BITSWAN_WORKSPACE_NAME")
    deployment_id = os.environ.get("BITSWAN_DEPLOYMENT_ID")
    stage = os.environ.get("BITSWAN_AUTOMATION_STAGE")
    domain = os.environ.get("BITSWAN_GITOPS_DOMAIN")

    if not all([workspace, deployment_id, domain]):
        return None

    # Get base deployment ID (strip stage suffix if present)
    base_id = deployment_id
    if stage and base_id.endswith(f"-{stage}"):
        base_id = base_id[: -(len(stage) + 1)]

    # Replace "backend" with "frontend"
    frontend_deployment_id = base_id.replace("-backend", "-frontend")

    # Build full deployment ID with stage
    full_deployment_id = (
        f"{frontend_deployment_id}-{stage}" if stage else frontend_deployment_id
    )

    return f"https://{workspace}-{full_deployment_id}.{domain}"


# Build CORS origins from environment, fallback to "*"
frontend_url = get_frontend_url()
cors_origins = [frontend_url] if frontend_url else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory counter
counter = {"count": 0}


@app.get("/")
async def root(claims: dict = Depends(validate_token)):
    return {"message": "Hello from FastAPI!", "user": claims.get("preferred_username")}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/count")
async def increment_count(claims: dict = Depends(validate_token)):
    counter["count"] += 1
    return {"count": counter["count"]}


@app.get("/count")
async def get_count(claims: dict = Depends(validate_token)):
    return {"count": counter["count"]}
