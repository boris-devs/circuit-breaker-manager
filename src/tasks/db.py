from redis import asyncio
from redis.asyncio import Redis as AsyncRedis
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from config.settings import Settings

settings = Settings()

_engine = None
_session_factory = None


def get_session_factory():
    global _engine, _session_factory
    if _engine is None:
        _engine = create_async_engine(url=settings.async_postgresql_url, poolclass=NullPool)
        _session_factory = async_sessionmaker(bind=_engine, class_=AsyncSession)
    return _session_factory


def get_redis_client() -> asyncio.Redis:
    redis_client = AsyncRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)
    return redis_client
