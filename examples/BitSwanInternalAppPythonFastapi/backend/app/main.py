import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.database import init_db, shutdown_db, async_session
from app.models import GalleryImage
from app import minio_client
from app.routers.internal import router as internal_router
from app.routers.public import router as public_router

logger = logging.getLogger(__name__)
app = FastAPI()


# --- Lifecycle ---


async def _preseed_gallery():
    """Preseed the bitswan logo into MinIO and the gallery_images table."""
    key = "bitswan-logo.svg"
    async with async_session() as db:
        exists = await db.execute(
            select(GalleryImage).where(GalleryImage.key == key)
        )
        if exists.scalar_one_or_none():
            return
    await minio_client.preseed_logo()
    async with async_session() as db:
        db.add(GalleryImage(
            key=key,
            title="BitSwan Logo",
            content_type="image/svg+xml",
            size=0,
            uploaded_by="system",
        ))
        await db.commit()


@app.on_event("startup")
async def startup():
    await init_db()
    await minio_client.ensure_bucket()
    await _preseed_gallery()


@app.on_event("shutdown")
async def shutdown():
    await shutdown_db()


# --- CORS ---

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Health ---


@app.get("/health")
def health():
    return {"status": "ok"}


# --- Routers ---

app.include_router(internal_router, prefix="/internal")
app.include_router(public_router, prefix="/public")
