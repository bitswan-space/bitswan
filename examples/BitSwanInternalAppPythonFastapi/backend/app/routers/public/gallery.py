from fastapi import Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import GalleryImage
from app import minio_client
from app.routers.public import router


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
