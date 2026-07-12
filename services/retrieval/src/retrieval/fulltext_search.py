"""Postgres full-text search over chunk text (to_tsvector / ts_rank)."""

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from rag_db.models import Chunk


async def fulltext_search(
    session: AsyncSession,
    query: str,
    k: int,
    predicates: list[ColumnElement[bool]],
) -> list[Chunk]:
    """Rank chunks by ``ts_rank`` against a plain-text query (best match first).

    Args:
        session: Active async session (Postgres required; ``to_tsvector``
            has no SQLite equivalent).
        query: Raw search text, parsed with ``plainto_tsquery``.
        k: Maximum number of chunks to return.
        predicates: AND-ed metadata predicates to apply before ranking.

    Returns:
        Chunks whose text matches the query, ranked best-first.
    """
    document = func.to_tsvector("english", Chunk.text)
    tsquery = func.plainto_tsquery("english", query)
    stmt = (
        select(Chunk)
        .where(document.op("@@")(tsquery), *predicates)
        .order_by(func.ts_rank(document, tsquery).desc())
        .limit(k)
    )
    return list(await session.scalars(stmt))
