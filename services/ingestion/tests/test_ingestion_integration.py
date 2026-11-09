"""Integration tests against real Postgres (skipped unless RAG_TEST_DB_URL is set)."""

import os
import subprocess
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from ingestion_test_helpers import FakeSqsClient, upload_payload
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ingestion.app import app
from ingestion.db import get_session
from ingestion.queue import ProcessingQueue, get_queue

DB_URL = os.environ.get("RAG_TEST_DB_URL", "")
pytestmark = pytest.mark.skipif(not DB_URL, reason="RAG_TEST_DB_URL not set")

REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def migrated_db() -> str:
    """Reset the test database schema via alembic downgrade/upgrade."""
    env = {**os.environ, "RAG_DATABASE_URL": DB_URL}
    ini = str(REPO_ROOT / "services" / "ingestion" / "alembic.ini")
    for target in [("downgrade", "base"), ("upgrade", "head")]:
        subprocess.run(
            ["uv", "run", "alembic", "-c", ini, *target],
            check=True,
            env=env,
            cwd=REPO_ROOT,
        )
    return DB_URL


@pytest.fixture
async def pg_client(migrated_db: str) -> AsyncIterator[AsyncClient]:
    """Yield an app client wired to the real Postgres test database."""
    engine = create_async_engine(migrated_db)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override() -> AsyncIterator[AsyncSession]:
        async with factory() as session:
            yield session

    app.dependency_overrides[get_session] = override
    app.dependency_overrides[get_queue] = lambda: ProcessingQueue("test-queue", FakeSqsClient())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
    await engine.dispose()


async def test_full_document_lifecycle_on_postgres(pg_client: AsyncClient) -> None:
    r1 = await pg_client.post("/documents", files=upload_payload("pg.txt", b"postgres v1"))
    assert r1.status_code == 201

    # Still pending, so a re-upload re-sends the message for the same document.
    dup = await pg_client.post("/documents", files=upload_payload("pg.txt", b"postgres v1"))
    assert dup.status_code == 201
    assert dup.json()["id"] == r1.json()["id"]

    r2 = await pg_client.post("/documents", files=upload_payload("pg.txt", b"postgres v2"))
    assert r2.status_code == 201
    assert r2.json()["version"] == 2

    listing = await pg_client.get("/documents")
    assert listing.json()["total"] >= 2

    doc_id = r1.json()["id"]
    assert (await pg_client.delete(f"/documents/{doc_id}")).status_code == 204
    assert (await pg_client.get(f"/documents/{doc_id}")).status_code == 404
