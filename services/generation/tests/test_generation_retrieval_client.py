"""Tests for the retrieval HTTP client (mocked transport, no network)."""

import httpx
import pytest

from generation.retrieval_client import RetrievalClient
from rag_common.exceptions import UpstreamError
from rag_contracts.search import SearchRequest


async def test_search_success() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"query": "hi", "items": []})

    client = RetrievalClient(
        base_url="http://retrieval", timeout=1.0, retries=2, transport=httpx.MockTransport(handler)
    )
    result = await client.search(SearchRequest(query="hi"))
    assert result.query == "hi"
    assert result.items == []


async def test_search_retries_then_succeeds() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 2:
            return httpx.Response(503)
        return httpx.Response(200, json={"query": "hi", "items": []})

    client = RetrievalClient(
        base_url="http://retrieval", timeout=1.0, retries=2, transport=httpx.MockTransport(handler)
    )
    result = await client.search(SearchRequest(query="hi"))
    assert calls["n"] == 2
    assert result.query == "hi"


async def test_search_exhausts_retries_raises_upstream_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    client = RetrievalClient(
        base_url="http://retrieval", timeout=1.0, retries=1, transport=httpx.MockTransport(handler)
    )
    with pytest.raises(UpstreamError):
        await client.search(SearchRequest(query="hi"))


async def test_search_transport_error_raises_upstream_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    client = RetrievalClient(
        base_url="http://retrieval", timeout=1.0, retries=0, transport=httpx.MockTransport(handler)
    )
    with pytest.raises(UpstreamError):
        await client.search(SearchRequest(query="hi"))


async def test_search_client_error_propagates_without_retry() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(422)

    client = RetrievalClient(
        base_url="http://retrieval", timeout=1.0, retries=2, transport=httpx.MockTransport(handler)
    )
    with pytest.raises(httpx.HTTPStatusError):
        await client.search(SearchRequest(query="hi"))
    assert calls["n"] == 1
