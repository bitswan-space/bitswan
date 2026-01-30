import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()


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
def root():
    return {"message": "Hello from FastAPI!"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/count")
def increment_count():
    counter["count"] += 1
    return {"count": counter["count"]}


@app.get("/count")
def get_count():
    return {"count": counter["count"]}
