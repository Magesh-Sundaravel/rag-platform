"""Postgres integration tests for hybrid search (skipped unless RAG_TEST_DB_URL)."""

import os
import subprocess
import uuid
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from rag_contracts.filters import FilterOp, MetadataFilter
from rag_contracts.search import SearchRequest
from rag_db.models import Chunk, Document
from rag_providers.embedding import FakeEmbeddingProvider
from retrieval.app import app
from retrieval.db import get_session
from retrieval.fulltext_search import fulltext_search
from retrieval.search import hybrid_search
from retrieval.vector_search import vector_knn

EMBEDDER = FakeEmbeddingProvider()

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


async def seed_chunks(factory: async_sessionmaker[AsyncSession]) -> dict[str, Chunk]:
    """Seed three chunks: one keyword-only match, one semantic-only match, one both."""
    texts = {
        "keyword": "The quokka is a small marsupial found on Rottnest Island.",
        "semantic": "A tiny hopping animal lives on an island near Perth.",
        "irrelevant": "Quarterly revenue grew twelve percent year over year.",
    }
    async with factory() as session:
        # The DB is shared by every test in this module; clear earlier seeds so
        # identical chunks don't tie with (and outrank) this test's chunks.
        await session.execute(delete(Document))  # chunks cascade via FK
        doc = Document(
            filename="animals.txt",
            content_type="text/plain",
            content_hash=uuid.uuid4().hex + uuid.uuid4().hex,
            version=1,
            status="processed",
            raw_text="animals",
        )
        session.add(doc)
        await session.flush()
        vectors = await EMBEDDER.embed(list(texts.values()))
        chunks = {}
        for i, ((key, text), vector) in enumerate(zip(texts.items(), vectors, strict=True)):
            chunk = Chunk(
                document_id=doc.id,
                chunk_index=i,
                text=text,
                token_count=len(text.split()),
                meta={"language": "en"},
                embedding=vector,
            )
            session.add(chunk)
            chunks[key] = chunk
        await session.commit()
        for chunk in chunks.values():
            await session.refresh(chunk)
        return chunks


async def test_fulltext_search_finds_keyword_match(
    pg_factory: async_sessionmaker[AsyncSession],
) -> None:
    chunks = await seed_chunks(pg_factory)
    async with pg_factory() as session:
        results = await fulltext_search(session, "quokka Rottnest", k=5, predicates=[])
    assert chunks["keyword"].id in {c.id for c in results}


async def test_vector_knn_finds_semantic_match(
    pg_factory: async_sessionmaker[AsyncSession],
) -> None:
    chunks = await seed_chunks(pg_factory)
    [query_vector] = await EMBEDDER.embed([chunks["semantic"].text])
    async with pg_factory() as session:
        results = await vector_knn(session, query_vector, k=1, predicates=[])
    assert results[0].id == chunks["semantic"].id


async def test_hybrid_search_fuses_both_signals(
    pg_factory: async_sessionmaker[AsyncSession],
) -> None:
    chunks = await seed_chunks(pg_factory)
    async with pg_factory() as session:
        items = await hybrid_search(
            session, EMBEDDER, SearchRequest(query="quokka Rottnest island", top_k=5)
        )
    # Only the keyword chunk matches FTS (plainto_tsquery ANDs terms), so it is
    # the one chunk in both ranked lists and must win the RRF fusion. Vector
    # KNN has no distance cutoff, so with three chunks all of them are returned.
    assert items[0].chunk_id == chunks["keyword"].id


async def test_hybrid_search_applies_metadata_filters(
    pg_factory: async_sessionmaker[AsyncSession],
) -> None:
    await seed_chunks(pg_factory)
    async with pg_factory() as session:
        items = await hybrid_search(
            session,
            EMBEDDER,
            SearchRequest(
                query="quokka",
                filters=[MetadataFilter(field="language", op=FilterOp.EQ, value="fr")],
            ),
        )
    assert items == []


async def test_search_endpoint(pg_factory: async_sessionmaker[AsyncSession]) -> None:
    chunks = await seed_chunks(pg_factory)

    async def override() -> AsyncIterator[AsyncSession]:
        async with pg_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/search", json={"query": "quokka Rottnest", "top_k": 5})
    app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body["query"] == "quokka Rottnest"
    ids = {item["chunk_id"] for item in body["items"]}
    assert str(chunks["keyword"].id) in ids
