"""SQS consumer tests on SQLite with an in-memory fake SQS client."""

import asyncio
import uuid
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from processing_test_helpers import FailingEmbedder, FakeSqs
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from processing.chunking import RecursiveCharacterChunker
from processing.worker import QueueConfig, handle_message, run_once, worker_loop
from rag_db.models import Base, Chunk, Document
from rag_providers.embedding import FakeEmbeddingProvider

CHUNKER = RecursiveCharacterChunker(200, 20)
EMBEDDER = FakeEmbeddingProvider(8)


@pytest.fixture
async def factory(tmp_path: Path) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    # File-backed SQLite so concurrent sessions (worker task + assertions)
    # get their own connections.
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'worker.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


@pytest.fixture
def sqs() -> FakeSqs:
    return FakeSqs()


def queue_for(sqs: FakeSqs, max_receive_count: int = 3) -> QueueConfig:
    return QueueConfig(client=sqs, url="q", wait_seconds=0, max_receive_count=max_receive_count)


def message_for(document_id: uuid.UUID) -> str:
    return f'{{"document_id": "{document_id}"}}'


async def seed(
    factory: async_sessionmaker[AsyncSession], *, raw_text: str = "# Title\nSome body text."
) -> Document:
    async with factory() as session:
        doc = Document(
            filename="a.md",
            content_type="text/markdown",
            content_hash=uuid.uuid4().hex + uuid.uuid4().hex,
            version=1,
            status="pending",
            raw_text=raw_text,
        )
        session.add(doc)
        await session.commit()
        return doc


async def test_run_once_returns_false_when_idle(
    factory: async_sessionmaker[AsyncSession], sqs: FakeSqs
) -> None:
    assert await run_once(factory, queue_for(sqs), CHUNKER, EMBEDDER) is False


async def test_success_marks_processed_and_deletes_message(
    factory: async_sessionmaker[AsyncSession], sqs: FakeSqs
) -> None:
    doc = await seed(factory)
    handle = sqs.put(message_for(doc.id))
    assert await run_once(factory, queue_for(sqs), CHUNKER, EMBEDDER) is True
    assert sqs.deleted == [handle]
    async with factory() as session:
        assert (await session.get(Document, doc.id)).status == "processed"  # type: ignore[union-attr]
        chunks = (await session.scalars(select(Chunk).where(Chunk.document_id == doc.id))).all()
        assert chunks
        assert chunks[0].meta["title"] == "Title"
        assert chunks[0].token_count > 0
        assert chunks[0].embedding is not None
        assert len(chunks[0].embedding) == 8


async def test_duplicate_delivery_replaces_chunks(
    factory: async_sessionmaker[AsyncSession], sqs: FakeSqs
) -> None:
    doc = await seed(factory)
    sqs.put(message_for(doc.id))
    sqs.put(message_for(doc.id))
    assert await run_once(factory, queue_for(sqs), CHUNKER, EMBEDDER) is True
    assert await run_once(factory, queue_for(sqs), CHUNKER, EMBEDDER) is True
    async with factory() as session:
        chunks = (await session.scalars(select(Chunk).where(Chunk.document_id == doc.id))).all()
        indexes = sorted(c.chunk_index for c in chunks)
        assert indexes == list(range(len(chunks)))


async def test_failure_retries_then_marks_failed_on_last_attempt(
    factory: async_sessionmaker[AsyncSession], sqs: FakeSqs
) -> None:
    doc = await seed(factory)
    sqs.put(message_for(doc.id))
    queue = queue_for(sqs, max_receive_count=2)

    assert await run_once(factory, queue, CHUNKER, FailingEmbedder()) is True
    assert sqs.deleted == []
    async with factory() as session:
        assert (await session.get(Document, doc.id)).status == "pending"  # type: ignore[union-attr]

    assert await run_once(factory, queue, CHUNKER, FailingEmbedder()) is True
    assert sqs.deleted == []  # left for SQS redrive to move to the DLQ
    async with factory() as session:
        assert (await session.get(Document, doc.id)).status == "failed"  # type: ignore[union-attr]


async def test_missing_document_is_acknowledged(
    factory: async_sessionmaker[AsyncSession], sqs: FakeSqs
) -> None:
    handle = sqs.put(message_for(uuid.uuid4()))
    assert await run_once(factory, queue_for(sqs), CHUNKER, EMBEDDER) is True
    assert sqs.deleted == [handle]


async def test_invalid_body_is_left_for_dlq(factory: async_sessionmaker[AsyncSession]) -> None:
    message = {"Body": "not json", "ReceiptHandle": "h", "Attributes": {}}
    assert await handle_message(factory, message, CHUNKER, EMBEDDER, max_receive_count=3) is False


async def test_worker_loop_processes_and_stops(
    factory: async_sessionmaker[AsyncSession], sqs: FakeSqs
) -> None:
    doc = await seed(factory)
    sqs.put(message_for(doc.id))
    stop = asyncio.Event()
    task = asyncio.create_task(
        worker_loop(factory, queue_for(sqs), CHUNKER, EMBEDDER, stop_event=stop)
    )
    for _ in range(100):
        await asyncio.sleep(0.01)
        if sqs.deleted:
            break
    stop.set()
    await asyncio.wait_for(task, timeout=2)
    async with factory() as session:
        assert (await session.get(Document, doc.id)).status == "processed"  # type: ignore[union-attr]


async def test_worker_loop_survives_non_sqs_errors(
    factory: async_sessionmaker[AsyncSession], sqs: FakeSqs, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("processing.worker.LOOP_ERROR_BACKOFF_SECONDS", 0)
    doc = await seed(factory)
    sqs.put(message_for(doc.id))
    sqs.fail_next_receive = RuntimeError("database is down")
    stop = asyncio.Event()
    task = asyncio.create_task(
        worker_loop(factory, queue_for(sqs), CHUNKER, EMBEDDER, stop_event=stop)
    )
    for _ in range(100):
        await asyncio.sleep(0.01)
        if sqs.deleted:
            break
    stop.set()
    await asyncio.wait_for(task, timeout=2)
    async with factory() as session:
        assert (await session.get(Document, doc.id)).status == "processed"  # type: ignore[union-attr]


async def test_last_attempt_failure_does_not_overwrite_processed(
    factory: async_sessionmaker[AsyncSession], sqs: FakeSqs
) -> None:
    # A duplicate delivery fails on its last attempt after another copy succeeded.
    doc = await seed(factory)
    async with factory() as session:
        stored = await session.get(Document, doc.id)
        assert stored is not None
        stored.status = "processed"
        await session.commit()
    sqs.put(message_for(doc.id))
    queue = queue_for(sqs, max_receive_count=1)
    assert await run_once(factory, queue, CHUNKER, FailingEmbedder()) is True
    async with factory() as session:
        assert (await session.get(Document, doc.id)).status == "processed"  # type: ignore[union-attr]
