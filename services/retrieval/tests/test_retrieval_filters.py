"""Tests for metadata predicate translation (SQLite-backed)."""

from collections.abc import AsyncIterator

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from rag_contracts.filters import FilterOp, MetadataFilter
from rag_db.models import Base, Chunk, Document
from retrieval.filters import metadata_predicates


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        doc = Document(
            filename="a.txt",
            content_type="text/plain",
            content_hash="a" * 64,
            version=1,
            status="processed",
            raw_text="text",
        )
        s.add(doc)
        await s.flush()
        for i, (lang, fname) in enumerate([("en", "a.txt"), ("en", "b.txt"), ("unknown", "c.txt")]):
            s.add(
                Chunk(
                    document_id=doc.id,
                    chunk_index=i,
                    text=f"chunk {i}",
                    token_count=2,
                    meta={"language": lang, "filename": fname, "title": "T"},
                )
            )
        await s.commit()
        yield s
    await engine.dispose()


async def filtered_texts(session: AsyncSession, filters: list[MetadataFilter]) -> list[str]:
    stmt = select(Chunk.text).where(*metadata_predicates(filters)).order_by(Chunk.chunk_index)
    return list(await session.scalars(stmt))


async def test_eq_filter(session: AsyncSession) -> None:
    result = await filtered_texts(session, [MetadataFilter(field="language", value="en")])
    assert result == ["chunk 0", "chunk 1"]


async def test_in_filter(session: AsyncSession) -> None:
    result = await filtered_texts(
        session,
        [MetadataFilter(field="filename", op=FilterOp.IN, value=["a.txt", "c.txt"])],
    )
    assert result == ["chunk 0", "chunk 2"]


async def test_filters_are_anded(session: AsyncSession) -> None:
    result = await filtered_texts(
        session,
        [
            MetadataFilter(field="language", value="en"),
            MetadataFilter(field="filename", op=FilterOp.IN, value=["b.txt", "c.txt"]),
        ],
    )
    assert result == ["chunk 1"]


async def test_no_match(session: AsyncSession) -> None:
    result = await filtered_texts(session, [MetadataFilter(field="language", value="fr")])
    assert result == []


def test_empty_filters_produce_no_predicates() -> None:
    assert metadata_predicates([]) == []
