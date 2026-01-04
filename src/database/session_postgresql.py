from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from config.settings import Settings

settings = Settings()

sync_postgresql_engine = create_engine(url=settings.sync_postgresql_url, echo=False)

async_postgresql_engine = create_async_engine(url=settings.async_postgresql_url, echo=False)

AsyncPostgresSessionLocal = async_sessionmaker(
    bind=async_postgresql_engine,
    class_=AsyncSession,
    autocommit=False,
    expire_on_commit=False,

)


async def get_postgresql_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncPostgresSessionLocal() as session:
        yield session
