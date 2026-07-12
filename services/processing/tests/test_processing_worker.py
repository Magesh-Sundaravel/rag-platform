"""Worker/job-queue tests on SQLite (claim, done, retry, dead-letter)."""

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from processing.chunking import RecursiveCharacterChunker
from processing.worker import claim_job, run_once, worker_loop
from rag_db.models import Base, Chunk, Document, Job

CHUNKER = RecursiveCharacterChunker(200, 20)


@pytest.fixture
async def factory(tmp_path: Path) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    # File-backed SQLite so concurrent sessions (worker task + assertions)
    # get their own connections.
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'worker.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


async def seed(
    factory: async_sessionmaker[AsyncSession],
    *,
    job_type: str = "process_document",
    raw_text: str = "# Title\nSome body text.",
    max_attempts: int = 3,
) -> tuple[Document, Job]:
    async with factory() as session:
        doc = Document(
            filename="a.md",
            content_type="text/markdown",
            content_hash="c" * 64,
            version=1,
            status="pending",
            raw_text=raw_text,
        )
        session.add(doc)
        await session.flush()
        job = Job(
            document_id=doc.id, job_type=job_type, status="pending", max_attempts=max_attempts
        )
        session.add(job)
        await session.commit()
        return doc, job


async def test_claim_empty_queue(factory: async_sessionmaker[AsyncSession]) -> None:
    async with factory() as session:
        assert await claim_job(session) is None


async def test_successful_job_marks_document_processed(
    factory: async_sessionmaker[AsyncSession],
) -> None:
    doc, job = await seed(factory)
    assert await run_once(factory, CHUNKER) is True
    async with factory() as session:
        assert (await session.get(Job, job.id)).status == "done"  # type: ignore[union-attr]
        assert (await session.get(Document, doc.id)).status == "processed"  # type: ignore[union-attr]
        chunks = (await session.scalars(select(Chunk).where(Chunk.document_id == doc.id))).all()
        assert chunks
        assert chunks[0].meta["title"] == "Title"
        assert chunks[0].token_count > 0


async def test_reprocessing_replaces_chunks(
    factory: async_sessionmaker[AsyncSession],
) -> None:
    doc, _job = await seed(factory)
    assert await run_once(factory, CHUNKER) is True
    async with factory() as session:
        session.add(Job(document_id=doc.id, job_type="process_document", status="pending"))
        await session.commit()
    assert await run_once(factory, CHUNKER) is True
    async with factory() as session:
        chunks = (await session.scalars(select(Chunk).where(Chunk.document_id == doc.id))).all()
        indexes = sorted(c.chunk_index for c in chunks)
        assert indexes == list(range(len(chunks)))


async def test_unknown_job_type_retries_then_dies(
    factory: async_sessionmaker[AsyncSession],
) -> None:
    doc, job = await seed(factory, job_type="bogus", max_attempts=2)
    assert await run_once(factory, CHUNKER) is True
    async with factory() as session:
        refreshed = await session.get(Job, job.id)
        assert refreshed is not None
        assert refreshed.status == "pending"
        assert refreshed.attempts == 1
        assert "unknown job type" in (refreshed.last_error or "")
    assert await run_once(factory, CHUNKER) is True
    async with factory() as session:
        refreshed = await session.get(Job, job.id)
        assert refreshed is not None
        assert refreshed.status == "dead"
        document = await session.get(Document, doc.id)
        assert document is not None
        assert document.status == "failed"


async def test_run_once_returns_false_when_idle(
    factory: async_sessionmaker[AsyncSession],
) -> None:
    assert await run_once(factory, CHUNKER) is False


async def test_worker_loop_processes_and_stops(
    factory: async_sessionmaker[AsyncSession],
) -> None:
    _doc, job = await seed(factory)
    stop = asyncio.Event()
    task = asyncio.create_task(worker_loop(factory, CHUNKER, poll_interval=0.01, stop_event=stop))
    for _ in range(100):
        await asyncio.sleep(0.01)
        async with factory() as session:
            refreshed = await session.get(Job, job.id)
            if refreshed is not None and refreshed.status == "done":
                break
    stop.set()
    await asyncio.wait_for(task, timeout=2)
    async with factory() as session:
        refreshed = await session.get(Job, job.id)
        assert refreshed is not None
        assert refreshed.status == "done"
