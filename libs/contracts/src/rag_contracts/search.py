"""Contracts for hybrid search requests/responses."""

import uuid
from typing import Any

from pydantic import BaseModel, Field

from rag_contracts.filters import MetadataFilter


class SearchRequest(BaseModel):
    """A hybrid search query."""

    query: str = Field(min_length=1)
    top_k: int = Field(default=10, ge=1, le=100)
    filters: list[MetadataFilter] = Field(default_factory=list)


class SearchResultItem(BaseModel):
    """One ranked chunk in a search response."""

    chunk_id: uuid.UUID
    document_id: uuid.UUID
    text: str
    score: float
    metadata: dict[str, Any]


class SearchResponse(BaseModel):
    """The fused, ranked results of a hybrid search query."""

    query: str
    items: list[SearchResultItem]
