"""
Pytest configuration and shared fixtures.

Test DB strategy:
  • A single in-memory (or test-only) Postgres DB is created per session.
  • Each test function wraps its work in a SAVEPOINT that is rolled back,
    so tests are fully isolated without dropping/recreating tables.

Requires: pytest-asyncio, httpx (for AsyncClient), a running Postgres.
Set TEST_DATABASE_URL env var to point at a test DB, e.g.:
    postgresql+asyncpg://postgres:postgres@localhost/shopify_test
"""
import asyncio
import os
import uuid
from typing import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost/shopify_test",
)

# ---------------------------------------------------------------------------
# Engine / session scoped to the test session
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def event_loop():
    """Single event loop for the whole test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Per-test DB session wrapped in a SAVEPOINT.
    All changes are rolled back after the test — no teardown SQL needed.
    """
    factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with factory() as session:
        await session.begin_nested()  # SAVEPOINT
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db) -> AsyncGenerator[AsyncClient, None]:
    """AsyncClient with the DB dependency overridden."""
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Data factories
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def store(db) -> "ShopifyStore":
    from app.models.db_models import ShopifyStore

    s = ShopifyStore(
        shop_domain=f"test-{uuid.uuid4().hex[:8]}.myshopify.com",
        access_token="shpat_test_token",
        scopes="read_orders,read_customers",
        currency="USD",
    )
    db.add(s)
    await db.flush()
    return s


@pytest_asyncio.fixture
async def customer(db, store) -> "Customer":
    from app.models.db_models import Customer

    c = Customer(
        store_id=store.id,
        shopify_customer_id=1001,
        email="buyer@example.com",
        total_spent=250.00,
        orders_count=3,
        currency="USD",
    )
    db.add(c)
    await db.flush()
    return c
