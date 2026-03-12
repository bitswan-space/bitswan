from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.auth import get_username_from_request
from app.database import get_db
from app.models import UserCounter
from app.routers.internal import router


@router.post("/count")
async def increment_count(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    username = get_username_from_request(request)
    stmt = (
        insert(UserCounter)
        .values(username=username, count=1)
        .on_conflict_do_update(
            index_elements=["username"],
            set_={"count": UserCounter.count + 1},
        )
        .returning(UserCounter.count)
    )
    result = await db.execute(stmt)
    await db.commit()
    count = result.scalar_one()
    return {"count": count, "user": username}


@router.get("/count")
async def get_count(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    username = get_username_from_request(request)
    result = await db.execute(
        select(UserCounter.count).where(UserCounter.username == username)
    )
    count = result.scalar_one_or_none()
    return {"count": count or 0, "user": username}
