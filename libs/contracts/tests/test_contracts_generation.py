"""Tests for the generation query request/response contracts."""

import uuid

import pytest
from pydantic import ValidationError

from rag_contracts.generation import Citation, QueryRequest, QueryResponse, Usage


def test_query_request_defaults() -> None:
    req = QueryRequest(question="what is RAG?")
    assert req.top_k == 5
    assert req.filters == []


def test_query_request_rejects_empty_question() -> None:
    with pytest.raises(ValidationError):
        QueryRequest(question="")


def test_query_request_rejects_too_long_question() -> None:
    with pytest.raises(ValidationError):
        QueryRequest(question="x" * 2001)


def test_query_request_rejects_out_of_range_top_k() -> None:
    with pytest.raises(ValidationError):
        QueryRequest(question="hi", top_k=0)
    with pytest.raises(ValidationError):
        QueryRequest(question="hi", top_k=21)


def test_query_response_round_trip() -> None:
    citation = Citation(chunk_id=uuid.uuid4(), document_id=uuid.uuid4(), snippet="a snippet")
    resp = QueryResponse(
        answer="the answer [1]",
        citations=[citation],
        usage=Usage(prompt_tokens=10, completion_tokens=5),
    )
    assert resp.citations[0].snippet == "a snippet"
    assert resp.usage.prompt_tokens == 10
