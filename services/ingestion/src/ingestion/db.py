"""Database wiring for the ingestion service."""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ingestion.config import Settings
from rag_db.session import create_engine, create_session_factory

_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the process-wide session factory, creating it lazily.

    Returns:
        The shared :class:`async_sessionmaker`.
    """
    global _session_factory
    if _session_factory is None:
        settings = Settings()
        _session_factory = create_session_factory(create_engine(settings.database_url))
    return _session_factory


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding one session per request.

    Yields:
        An :class:`AsyncSession` that is closed after the request.
    """
    async with get_session_factory()() as session:
        yield session
