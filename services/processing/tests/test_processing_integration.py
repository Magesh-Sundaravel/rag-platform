"""Postgres integration test for the SQS consumer (skipped unless RAG_TEST_DB_URL)."""

import os
import subprocess
import uuid
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from processing_test_helpers import FakeSqs
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from processing.chunking import RecursiveCharacterChunker
from processing.worker import QueueConfig, run_once
from rag_db.models import Chunk, Document
from rag_providers.embedding import FakeEmbeddingProvider

CHUNKER = RecursiveCharacterChunker(200, 20)
EMBEDDER = FakeEmbeddingProvider()  # 1024 dims to satisfy vector(1024)

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


async def seed_document(factory: async_sessionmaker[AsyncSession]) -> uuid.UUID:
    async with factory() as session:
        doc = Document(
            filename=f"sqs-{uuid.uuid4().hex[:8]}.txt",
            content_type="text/plain",
            content_hash=uuid.uuid4().hex + uuid.uuid4().hex,
            version=1,
            status="pending",
            raw_text="The text of the document is right here and it is fine.",
        )
        session.add(doc)
        await session.commit()
        return doc.id


async def test_run_once_processes_on_postgres(
    pg_factory: async_sessionmaker[AsyncSession],
) -> None:
    doc_id = await seed_document(pg_factory)
    sqs = FakeSqs()
    sqs.put(f'{{"document_id": "{doc_id}"}}')
    queue = QueueConfig(client=sqs, url="q", wait_seconds=0, max_receive_count=3)
    assert await run_once(pg_factory, queue, CHUNKER, EMBEDDER) is True
    async with pg_factory() as session:
        doc = await session.get(Document, doc_id)
        assert doc is not None
        assert doc.status == "processed"
        chunks = (await session.scalars(select(Chunk).where(Chunk.document_id == doc.id))).all()
        assert chunks
        assert chunks[0].meta["filename"] == doc.filename
        assert chunks[0].embedding is not None
        assert len(chunks[0].embedding) == 1024
