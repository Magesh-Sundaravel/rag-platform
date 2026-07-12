"""Tests for grounded prompt construction and citation extraction."""

import uuid

from generation.prompting import build_prompt, extract_citations
from rag_contracts.search import SearchResultItem


def _chunk(text: str) -> SearchResultItem:
    return SearchResultItem(
        chunk_id=uuid.uuid4(), document_id=uuid.uuid4(), text=text, score=1.0, metadata={}
    )


def test_build_prompt_numbers_context_blocks() -> None:
    chunks = [_chunk("first chunk"), _chunk("second chunk")]
    prompt = build_prompt("what happened?", chunks)
    assert "[1] first chunk" in prompt
    assert "[2] second chunk" in prompt
    assert "Question: what happened?" in prompt


def test_build_prompt_no_chunks() -> None:
    prompt = build_prompt("what happened?", [])
    assert "Question: what happened?" in prompt


def test_extract_citations_maps_markers_in_order() -> None:
    chunks = [_chunk("first"), _chunk("second"), _chunk("third")]
    citations = extract_citations("the answer is [2] because of [1]", chunks)
    assert [c.snippet for c in citations] == ["second", "first"]


def test_extract_citations_dedupes() -> None:
    chunks = [_chunk("first")]
    citations = extract_citations("[1] and again [1]", chunks)
    assert len(citations) == 1


def test_extract_citations_ignores_out_of_range() -> None:
    chunks = [_chunk("first")]
    citations = extract_citations("see [1] and [5]", chunks)
    assert len(citations) == 1
    assert citations[0].snippet == "first"


def test_extract_citations_no_markers() -> None:
    chunks = [_chunk("first")]
    assert extract_citations("no citations here", chunks) == []


def test_extract_citations_truncates_snippet() -> None:
    chunks = [_chunk("x" * 300)]
    citations = extract_citations("[1]", chunks)
    assert len(citations[0].snippet) == 200
