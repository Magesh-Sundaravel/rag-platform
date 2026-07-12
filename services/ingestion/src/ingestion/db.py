"""Lazy database wiring and the FastAPI session dependency."""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ingestion.config import Settings
from rag_db.session import create_engine, create_session_factory

_session_factory: async_sessionmaker[AsyncSession] | None = None


def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Create the session factory on first use (import stays connection-free)."""
    global _session_factory
    if _session_factory is None:
        _session_factory = create_session_factory(create_engine(Settings().database_url))
    return _session_factory


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding one session per request.

    Yields:
        An :class:`AsyncSession` that is closed when the request ends.
    """
    async with _get_session_factory()() as session:
        yield session
