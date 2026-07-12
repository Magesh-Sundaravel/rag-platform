"""HTTP routes for the retrieval service."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from rag_contracts.search import SearchRequest, SearchResponse
from rag_providers.embedding import EmbeddingProvider
from rag_providers.factory import build_embedding_provider
from retrieval.config import Settings
from retrieval.db import get_session
from retrieval.search import hybrid_search

router = APIRouter(tags=["search"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_embedder() -> EmbeddingProvider:
    """Build the configured embedding provider for query embedding."""
    return build_embedding_provider(Settings().embedding_provider)


EmbedderDep = Annotated[EmbeddingProvider, Depends(get_embedder)]


@router.post("/search")
async def search(
    request: SearchRequest, session: SessionDep, embedder: EmbedderDep
) -> SearchResponse:
    """Run hybrid (vector + full-text) search fused with RRF."""
    items = await hybrid_search(session, embedder, request)
    return SearchResponse(query=request.query, items=items)
