"""Tests for rag_db session helpers and model metadata."""

from sqlalchemy import inspect

from rag_db.models import Base, Chunk, Document
from rag_db.session import create_engine, create_session_factory


def test_models_registered() -> None:
    tables = Base.metadata.tables
    assert "documents" in tables
    assert "jobs" not in tables


def test_document_defaults() -> None:
    doc = Document(
        filename="a.txt",
        content_type="text/plain",
        content_hash="0" * 64,
        raw_text="x",
    )
    mapper = inspect(Document)
    assert mapper.columns["content_hash"].unique
    assert doc.filename == "a.txt"


def test_chunk_fk_cascade() -> None:
    fk = next(iter(inspect(Chunk).columns["document_id"].foreign_keys))
    assert fk.ondelete == "CASCADE"


async def test_engine_and_session_factory() -> None:
    engine = create_engine("sqlite+aiosqlite://")
    factory = create_session_factory(engine)
    async with factory() as session:
        assert session.bind is engine
    await engine.dispose()
