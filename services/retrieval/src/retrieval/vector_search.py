"""Vector KNN search over chunk embeddings (pgvector cosine distance)."""

from sqlalchemy import ColumnElement, select
from sqlalchemy.ext.asyncio import AsyncSession

from rag_db.models import Chunk


async def vector_knn(
    session: AsyncSession,
    query_vector: list[float],
    k: int,
    predicates: list[ColumnElement[bool]],
) -> list[Chunk]:
    """Rank chunks by cosine distance to a query vector (nearest first).

    Args:
        session: Active async session (Postgres + pgvector required).
        query_vector: The embedded search query.
        k: Maximum number of chunks to return.
        predicates: AND-ed metadata predicates to apply before ranking.

    Returns:
        Chunks ordered nearest-first.
    """
    stmt = (
        select(Chunk)
        .where(Chunk.embedding.is_not(None), *predicates)
        .order_by(Chunk.embedding.cosine_distance(query_vector))
        .limit(k)
    )
    return list(await session.scalars(stmt))
