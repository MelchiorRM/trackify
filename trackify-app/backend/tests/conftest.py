"""
Test substrate: SQLite (aiosqlite) in place of Postgres, fakeredis in place
of Redis. Production code targets asyncpg + real Redis (see app/database.py,
app/redis.py) — these fixtures only override what get_db/get_redis resolve
to for the lifetime of each test, via FastAPI's dependency_overrides.

Note: httpx's ASGITransport does not invoke the app's lifespan (which calls
the real redis_client.ping()), so these tests never touch real Redis even
indirectly.
"""

import fakeredis.aioredis
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.dependencies import get_db, get_redis
from app.main import app


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    test_session_local = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with test_session_local() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)
    await engine.dispose()


@pytest_asyncio.fixture
async def fake_redis():
    redis_client = fakeredis.aioredis.FakeRedis(decode_responses=True)

    async def override_get_redis():
        return redis_client

    app.dependency_overrides[get_redis] = override_get_redis
    yield redis_client
    app.dependency_overrides.pop(get_redis, None)
    await redis_client.aclose()


@pytest_asyncio.fixture
async def client(db_session, fake_redis):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
