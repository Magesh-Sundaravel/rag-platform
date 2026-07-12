"""Integration tests against real Postgres; skipped unless RAG_TEST_DB_URL is set."""

import asyncio
import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

pytestmark = pytest.mark.skipif(
    not os.environ.get("RAG_TEST_DB_URL"),
    reason="RAG_TEST_DB_URL not set; Postgres integration tests run in CI",
)

ALEMBIC_INI = Path(__file__).parents[1] / "alembic.ini"


def _alembic_config(url: str) -> Config:
    cfg = Config(str(ALEMBIC_INI))
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


async def _crud_round_trip(url: str) -> None:
    from ingestion import repository
    from rag_common.exceptions import ConflictError
    from rag_db.session import create_engine, create_session_factory

    engine = create_engine(url)
    factory = create_session_factory(engine)
    async with factory() as session:
        doc = await repository.create_document(
            session,
            filename="integration.txt",
            content_type="text/plain",
            data=b"integration",
            raw_text="integration",
        )
        assert doc.version == 1
        with pytest.raises(ConflictError):
            await repository.create_document(
                session,
                filename="integration.txt",
                content_type="text/plain",
                data=b"integration",
                raw_text="integration",
            )
        await session.rollback()
        await repository.delete_document(session, doc.id)
    await engine.dispose()


def test_upgrade_head_then_crud_then_downgrade() -> None:
    url = os.environ["RAG_TEST_DB_URL"]
    cfg = _alembic_config(url)
    command.upgrade(cfg, "head")
    asyncio.run(_crud_round_trip(url))
    command.downgrade(cfg, "base")
