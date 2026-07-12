"""Postgres integration tests for job claiming (skipped unless RAG_TEST_DB_URL)."""

import os
import subprocess
import uuid
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from processing.chunking import RecursiveCharacterChunker
from processing.worker import claim_job, run_once
from rag_db.models import Chunk, Document, Job

CHUNKER = RecursiveCharacterChunker(200, 20)

DB_URL = os.environ.get("RAG_TEST_DB_URL", "")
pytestmark = pytest.mark.skipif(not DB_URL, reason="RAG_TEST_DB_URL not set")

REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def migrated_db() -> str:
    env = {**os.environ, "RAG_DATABASE_URL": DB_URL}
    ini = str(REPO_ROOT / "services" / "ingestion" / "alembic.ini")
    for target in [("downgrade", "base"), ("upgrade", "head")]:
        subprocess.run(
            ["uv", "run", "alembic", "-c", ini, *target], check=True, env=env, cwd=REPO_ROOT
        )
    return DB_URL


@pytest.fixture
async def pg_factory(migrated_db: str) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(migrated_db)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


async def seed_job(factory: async_sessionmaker[AsyncSession]) -> uuid.UUID:
    async with factory() as session:
        doc = Document(
            filename=f"claim-{uuid.uuid4().hex[:8]}.txt",
            content_type="text/plain",
            content_hash=uuid.uuid4().hex + uuid.uuid4().hex,
            version=1,
            status="pending",
            raw_text="The text of the document is right here and it is fine.",
        )
        session.add(doc)
        await session.flush()
        job = Job(document_id=doc.id, job_type="process_document", status="pending")
        session.add(job)
        await session.commit()
        return job.id


async def test_skip_locked_prevents_double_claim(
    pg_factory: async_sessionmaker[AsyncSession],
) -> None:
    first = await seed_job(pg_factory)
    second = await seed_job(pg_factory)

    async with pg_factory() as s1, pg_factory() as s2:
        # Hold a row lock on the oldest pending job without committing.
        locked = await s1.scalar(
            select(Job)
            .where(Job.status == "pending")
            .order_by(Job.created_at)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        assert locked is not None
        # A concurrent claim must skip the locked row and take the other job.
        claimed = await claim_job(s2)
        assert claimed is not None
        assert claimed.id != locked.id
        assert {locked.id, claimed.id} <= {first, second}
        await s1.rollback()


async def test_run_once_processes_on_postgres(
    pg_factory: async_sessionmaker[AsyncSession],
) -> None:
    while await run_once(pg_factory, CHUNKER):
        pass
    job_id = await seed_job(pg_factory)
    assert await run_once(pg_factory, CHUNKER) is True
    async with pg_factory() as session:
        job = await session.get(Job, job_id)
        assert job is not None
        assert job.status == "done"
        doc = await session.get(Document, job.document_id)
        assert doc is not None
        assert doc.status == "processed"
        chunks = (await session.scalars(select(Chunk).where(Chunk.document_id == doc.id))).all()
        assert chunks
        assert chunks[0].meta["filename"] == doc.filename
