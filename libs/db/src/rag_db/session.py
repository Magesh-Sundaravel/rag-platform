"""Async engine and session-factory helpers shared by all services."""

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def create_engine(url: str, *, echo: bool = False) -> AsyncEngine:
    """Create an async engine for the given database URL.

    Args:
        url: SQLAlchemy async URL (e.g. ``postgresql+asyncpg://...``).
        echo: Emit SQL to the log (development only).

    Returns:
        A configured :class:`AsyncEngine`.
    """
    return create_async_engine(url, echo=echo, pool_pre_ping=True)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create a session factory bound to the given engine.

    Args:
        engine: The async engine to bind sessions to.

    Returns:
        An :class:`async_sessionmaker` producing non-expiring sessions.
    """
    return async_sessionmaker(engine, expire_on_commit=False)
