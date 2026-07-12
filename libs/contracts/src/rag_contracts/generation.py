"""Contracts for grounded-generation requests/responses."""

import uuid

from pydantic import BaseModel, Field

from rag_contracts.filters import MetadataFilter


class QueryRequest(BaseModel):
    """A question to answer using retrieval-grounded generation."""

    question: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)
    filters: list[MetadataFilter] = Field(default_factory=list)


class Citation(BaseModel):
    """A source chunk referenced by the generated answer."""

    chunk_id: uuid.UUID
    document_id: uuid.UUID
    snippet: str


class Usage(BaseModel):
    """Token usage reported by the generation provider."""

    prompt_tokens: int
    completion_tokens: int


class QueryResponse(BaseModel):
    """A grounded answer with its supporting citations."""

    answer: str
    citations: list[Citation]
    usage: Usage
