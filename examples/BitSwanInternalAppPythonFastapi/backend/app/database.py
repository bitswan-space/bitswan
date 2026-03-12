import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


def get_database_url() -> str:
    pg_host = os.environ.get("POSTGRES_HOST", "localhost")
    pg_user = os.environ.get("POSTGRES_USER", "admin")
    pg_password = os.environ.get("POSTGRES_PASSWORD", "")
    pg_db = os.environ.get("POSTGRES_DB", "postgres")
    pg_port = os.environ.get("POSTGRES_PORT", "5432")
    return f"postgresql+asyncpg://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"


engine = create_async_engine(get_database_url(), pool_size=5, max_overflow=0)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def init_db():
    from app import models  # noqa: F401 — ensure models are registered

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def shutdown_db():
    await engine.dispose()


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session
