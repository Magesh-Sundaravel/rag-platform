"""HTTP routes for the generation service."""

from typing import Annotated

from fastapi import APIRouter, Depends

from generation.config import Settings
from generation.prompting import build_prompt, extract_citations
from generation.retrieval_client import RetrievalClient
from rag_common.exceptions import InvalidInputError
from rag_contracts.generation import QueryRequest, QueryResponse, Usage
from rag_contracts.search import SearchRequest
from rag_guardrails.pii import redact_pii
from rag_guardrails.prompt_injection import detect_prompt_injection
from rag_providers.factory import build_generation_provider
from rag_providers.generation import GenerationProvider

router = APIRouter(tags=["generation"])

_NO_CONTEXT_ANSWER = "I couldn't find any relevant information to answer this question."


def get_retrieval_client() -> RetrievalClient:
    """Build the configured retrieval HTTP client."""
    settings = Settings()
    return RetrievalClient(
        base_url=settings.retrieval_url,
        timeout=settings.request_timeout_seconds,
        retries=settings.retrieval_retries,
    )


def get_generation_provider() -> GenerationProvider:
    """Build the configured generation provider."""
    return build_generation_provider(Settings().generation_provider)


RetrievalClientDep = Annotated[RetrievalClient, Depends(get_retrieval_client)]
GenerationProviderDep = Annotated[GenerationProvider, Depends(get_generation_provider)]


@router.post("/query")
async def query(
    request: QueryRequest, retrieval_client: RetrievalClientDep, generator: GenerationProviderDep
) -> QueryResponse:
    """Answer a question grounded in retrieved chunks, with citations."""
    if detect_prompt_injection(request.question):
        raise InvalidInputError("question was flagged as a potential prompt injection")

    search_response = await retrieval_client.search(
        SearchRequest(query=request.question, top_k=request.top_k, filters=request.filters)
    )
    if not search_response.items:
        return QueryResponse(
            answer=_NO_CONTEXT_ANSWER,
            citations=[],
            usage=Usage(prompt_tokens=0, completion_tokens=0),
        )

    prompt = build_prompt(request.question, search_response.items)
    result = await generator.generate(prompt)
    citations = extract_citations(result.text, search_response.items)
    return QueryResponse(
        answer=redact_pii(result.text),
        citations=citations,
        usage=Usage(prompt_tokens=result.prompt_tokens, completion_tokens=result.completion_tokens),
    )
