"""Tests for the search request/response contracts."""

import uuid

import pytest
from pydantic import ValidationError

from rag_contracts.search import SearchRequest, SearchResponse, SearchResultItem


def test_search_request_defaults() -> None:
    req = SearchRequest(query="hello")
    assert req.top_k == 10
    assert req.filters == []


def test_search_request_rejects_empty_query() -> None:
    with pytest.raises(ValidationError):
        SearchRequest(query="")


def test_search_request_rejects_out_of_range_top_k() -> None:
    with pytest.raises(ValidationError):
        SearchRequest(query="hello", top_k=0)
    with pytest.raises(ValidationError):
        SearchRequest(query="hello", top_k=101)


def test_search_response_round_trip() -> None:
    item = SearchResultItem(
        chunk_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        text="chunk text",
        score=0.5,
        metadata={"language": "en"},
    )
    resp = SearchResponse(query="hello", items=[item])
    assert resp.items[0].text == "chunk text"
