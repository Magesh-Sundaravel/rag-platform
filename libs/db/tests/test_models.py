"""Round-trip the ORM models through the session helpers on SQLite."""

from pathlib import Path

from sqlalchemy import select

from rag_db.models import Base, Document, Job
from rag_db.session import create_engine, create_session_factory


async def test_document_and_job_round_trip(tmp_path: Path) -> None:
    engine = create_engine(f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = create_session_factory(engine)
    async with factory() as session:
        doc = Document(
            filename="a.txt",
            content_type="text/plain",
            content_hash="c" * 64,
            raw_text="hello",
        )
        session.add(doc)
        await session.flush()
        session.add(Job(document_id=doc.id, job_type="process_document"))
        await session.commit()

        loaded = (await session.scalars(select(Document))).one()
        assert loaded.version == 1
        assert loaded.status == "pending"
        job = (await session.scalars(select(Job))).one()
        assert job.document_id == loaded.id
        assert job.attempts == 0

    await engine.dispose()
