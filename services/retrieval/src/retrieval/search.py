"""Hybrid search orchestration: vector KNN + full-text, fused with RRF."""

from sqlalchemy.ext.asyncio import AsyncSession

from rag_contracts.search import SearchRequest, SearchResultItem
from rag_db.models import Chunk
from rag_providers.embedding import EmbeddingProvider
from retrieval.filters import metadata_predicates
from retrieval.fulltext_search import fulltext_search
from retrieval.hybrid import reciprocal_rank_fusion
from retrieval.vector_search import vector_knn

# Over-fetch each ranked list beyond top_k so fusion has enough candidates
# to re-rank from (a chunk strong in only one signal can still win).
CANDIDATE_MULTIPLIER = 4


async def hybrid_search(
    session: AsyncSession, embedder: EmbeddingProvider, request: SearchRequest
) -> list[SearchResultItem]:
    """Run vector + full-text search and fuse the results with RRF.

    Args:
        session: Active async session (Postgres required).
        embedder: Provider used to embed the query text.
        request: The validated search request.

    Returns:
        Up to ``request.top_k`` results, best-first.
    """
    predicates = metadata_predicates(request.filters)
    candidate_k = request.top_k * CANDIDATE_MULTIPLIER
    [query_vector] = await embedder.embed([request.query])

    # Async SQLAlchemy sessions do not permit concurrent DB operations on the
    # same session, so run the two searches back-to-back.
    vector_chunks = await vector_knn(session, query_vector, candidate_k, predicates)
    text_chunks = await fulltext_search(session, request.query, candidate_k, predicates)
    by_id: dict[object, Chunk] = {c.id: c for c in [*vector_chunks, *text_chunks]}

    scores = reciprocal_rank_fusion([[c.id for c in vector_chunks], [c.id for c in text_chunks]])
    ranked_ids = sorted(scores, key=lambda cid: scores[cid], reverse=True)[: request.top_k]

    return [
        SearchResultItem(
            chunk_id=chunk.id,
            document_id=chunk.document_id,
            text=chunk.text,
            score=scores[chunk.id],
            metadata=chunk.meta,
        )
        for chunk in (by_id[cid] for cid in ranked_ids)
    ]
