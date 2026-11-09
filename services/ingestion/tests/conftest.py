"""Shared fixtures: SQLite-backed app client for ingestion API tests."""

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from ingestion_test_helpers import FakeSqsClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from ingestion.app import app
from ingestion.db import get_session
from ingestion.queue import ProcessingQueue, get_queue
from rag_db.models import Base


@pytest.fixture
def sqs() -> FakeSqsClient:
    """Yield the fake SQS client injected into the app."""
    return FakeSqsClient()


@pytest.fixture
async def session_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """Yield a session factory bound to a fresh in-memory SQLite database."""
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


@pytest.fixture
async def client(
    session_factory: async_sessionmaker[AsyncSession], sqs: FakeSqsClient
) -> AsyncIterator[AsyncClient]:
    """Yield an httpx client for the ingestion app with test DB and fake SQS injected."""

    async def override() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override
    app.dependency_overrides[get_queue] = lambda: ProcessingQueue("test-queue", sqs)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
