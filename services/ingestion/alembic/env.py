"""Alembic async environment for the shared MVP database (ADR-0004)."""

import asyncio
import os

from alembic import context
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from rag_db.models import Base

config = context.config
target_metadata = Base.metadata


def _database_url() -> str:
    """Resolve the database URL from the environment."""
    url = os.environ.get("RAG_DATABASE_URL") or os.environ.get("RAG_TEST_DB_URL")
    if not url:
        raise RuntimeError("set RAG_DATABASE_URL (or RAG_TEST_DB_URL) to run migrations")
    return url


def do_run_migrations(connection: Connection) -> None:
    """Run migrations on a sync connection provided by run_sync."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations."""
    engine = create_async_engine(_database_url())
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


def run_migrations_online() -> None:
    """Entry point for online migrations."""
    asyncio.run(run_async_migrations())


run_migrations_online()
