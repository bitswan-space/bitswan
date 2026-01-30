import os

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import User, get_current_user

app = FastAPI()

# Get allowed origins from environment variable (comma-separated)
# Falls back to allowing all origins if not set
cors_origins_env = os.environ.get("CORS_ALLOWED_ORIGINS", "*")
if cors_origins_env == "*":
    cors_origins = ["*"]
else:
    cors_origins = [origin.strip() for origin in cors_origins_env.split(",")]

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
async def increment_count(user: User = Depends(get_current_user)):
    counter["count"] += 1
    return {"count": counter["count"], "user": user.username}


@app.get("/count")
async def get_count(user: User = Depends(get_current_user)):
    return {"count": counter["count"], "user": user.username}
