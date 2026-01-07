from contextlib import asynccontextmanager

import pytest

from fastapi import websockets, FastAPI
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from fakeredis.aioredis import FakeRedis

from database.session_redis import get_redis_cache
from main import app
from database import Base, get_db
from services.service_status_cache import RedisServiceStatusCache

SQLITE_IN_MEMORY_DB = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture
def websocket_manager():
    return websockets


@pytest.fixture
async def _redis_client():
    redis_server = FakeRedis(decode_responses=True)
    return redis_server


@pytest.fixture(scope="session")
async def async_db_engine():
    engine = create_async_engine(SQLITE_IN_MEMORY_DB, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(async_db_engine):
    session_local = async_sessionmaker(
        bind=async_db_engine,
        expire_on_commit=False,
        class_=AsyncSession
    )
    async with session_local() as session:
        yield session
        await session.rollback()


@asynccontextmanager
async def mocked_lifespan(_: FastAPI):
    print("Started mocked lifespan")
    yield
    print("Finished mocked lifespan")


@pytest.fixture
async def _app():
    original_lifespan = app.router.lifespan_context
    app.router.lifespan_context = mocked_lifespan

    yield app

    app.router.lifespan_context = original_lifespan


@pytest.fixture()
async def client(db_session, _redis_client, websocket_manager):
    async def _get_test_db():
        yield db_session

    async def _get_redis_cache():
        yield RedisServiceStatusCache(redis_client=_redis_client)

    app.dependency_overrides[get_db] = _get_test_db
    app.dependency_overrides[get_redis_cache] = _get_redis_cache
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test/api/v1") as ac:
        yield ac

    app.dependency_overrides.clear()
