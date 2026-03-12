import os

from fastapi import Depends, HTTPException, UploadFile, File
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.auth import get_username_from_request
from app.database import get_db
from app.models import GalleryImage
from app import minio_client
from app.routers.internal import router


@router.get("/gallery")
async def list_gallery(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(GalleryImage).order_by(GalleryImage.created_at.desc())
    )
    images = result.scalars().all()
    return {
        "images": [
            {
                "id": img.id,
                "key": img.key,
                "title": img.title,
                "content_type": img.content_type,
                "size": img.size,
                "uploaded_by": img.uploaded_by,
                "created_at": img.created_at.isoformat(),
            }
            for img in images
        ]
    }


@router.get("/gallery/{filename:path}")
async def get_gallery_image(filename: str):
    try:
        data, content_type = await minio_client.get_file(filename)
    except Exception:
        raise HTTPException(status_code=404, detail="Image not found")
    return Response(content=data, media_type=content_type)


@router.post("/gallery/upload")
async def upload_gallery_image(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    data = await file.read()
    key = file.filename
    await minio_client.upload_file(key, data, file.content_type)
    username = get_username_from_request(request)
    title = os.path.splitext(key)[0].replace("-", " ").replace("_", " ").title()
    record = GalleryImage(
        key=key,
        title=title,
        content_type=file.content_type,
        size=len(data),
        uploaded_by=username,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return {
        "id": record.id,
        "key": record.key,
        "title": record.title,
        "uploaded_by": record.uploaded_by,
        "size": record.size,
    }


@router.delete("/gallery/{filename:path}")
async def delete_gallery_image(
    filename: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(GalleryImage).where(GalleryImage.key == filename)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Image not found")
    await minio_client.delete_file(filename)
    await db.delete(record)
    await db.commit()
    return {"deleted": filename}
