"""API tests for POST /query (mocked retrieval transport, fake generation)."""

import uuid
from collections.abc import AsyncIterator

import httpx
import pytest

from generation.app import app
from generation.retrieval_client import RetrievalClient
from generation.routes import get_generation_provider, get_retrieval_client
from rag_providers.generation import FakeGenerationProvider

CHUNK_ID = uuid.uuid4()
DOCUMENT_ID = uuid.uuid4()


def _search_response_with_items() -> dict[str, object]:
    return {
        "query": "what is the capital of france?",
        "items": [
            {
                "chunk_id": str(CHUNK_ID),
                "document_id": str(DOCUMENT_ID),
                "text": "Paris is the capital of France.",
                "score": 0.9,
                "metadata": {},
            }
        ],
    }


@pytest.fixture
async def client_with_items() -> AsyncIterator[httpx.AsyncClient]:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_search_response_with_items())

    retrieval_client = RetrievalClient(
        base_url="http://retrieval", timeout=1.0, retries=0, transport=httpx.MockTransport(handler)
    )
    app.dependency_overrides[get_retrieval_client] = lambda: retrieval_client
    app.dependency_overrides[get_generation_provider] = FakeGenerationProvider
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
async def client_with_no_items() -> AsyncIterator[httpx.AsyncClient]:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"query": "anything", "items": []})

    retrieval_client = RetrievalClient(
        base_url="http://retrieval", timeout=1.0, retries=0, transport=httpx.MockTransport(handler)
    )
    app.dependency_overrides[get_retrieval_client] = lambda: retrieval_client
    app.dependency_overrides[get_generation_provider] = FakeGenerationProvider
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


async def test_query_returns_grounded_answer_with_citations(
    client_with_items: httpx.AsyncClient,
) -> None:
    resp = await client_with_items.post("/query", json={"question": "what is the capital?"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["citations"] == [
        {
            "chunk_id": str(CHUNK_ID),
            "document_id": str(DOCUMENT_ID),
            "snippet": "Paris is the capital of France.",
        }
    ]
    assert "Paris is the capital of France." in body["answer"]
    assert body["usage"]["prompt_tokens"] > 0


async def test_query_no_context_skips_generation(client_with_no_items: httpx.AsyncClient) -> None:
    resp = await client_with_no_items.post("/query", json={"question": "anything"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["citations"] == []
    assert body["usage"] == {"prompt_tokens": 0, "completion_tokens": 0}


async def test_query_rejects_empty_question(client_with_items: httpx.AsyncClient) -> None:
    resp = await client_with_items.post("/query", json={"question": ""})
    assert resp.status_code == 422


async def test_query_retrieval_outage_returns_upstream_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    retrieval_client = RetrievalClient(
        base_url="http://retrieval", timeout=1.0, retries=0, transport=httpx.MockTransport(handler)
    )
    app.dependency_overrides[get_retrieval_client] = lambda: retrieval_client
    app.dependency_overrides[get_generation_provider] = FakeGenerationProvider
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.post("/query", json={"question": "anything"})
    app.dependency_overrides.clear()
    assert resp.status_code == 502
    assert resp.json()["error"]["code"] == "upstream_error"
