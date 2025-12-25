from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from config.settings import Settings

settings = Settings()

POSTGRESQL_DATABASE_URL = (f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@"
                           f"{settings.POSTGRES_HOST}:{settings.POSTGRES_DB_PORT}/{settings.POSTGRES_DB}")

postgresql_engine = create_async_engine(url=POSTGRESQL_DATABASE_URL, echo=False)

AsyncPostgresSessionLocal = async_sessionmaker(
    bind=postgresql_engine,
    class_=AsyncSession,
    autocommit=False,
    expire_on_commit=False,

)
sync_postgresql_engine = POSTGRESQL_DATABASE_URL.replace("postgresql+asyncpg", "postgresql")
SyncPostgresSessionLocal = create_engine(url=sync_postgresql_engine, echo=False)


async def get_postgresql_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncPostgresSessionLocal() as session:
        yield session
