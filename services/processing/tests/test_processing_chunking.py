"""Invariant tests for chunking strategies."""

from itertools import pairwise

import pytest

from processing.chunking import FixedSizeChunker, RecursiveCharacterChunker, build_chunker
from rag_common.exceptions import InvalidInputError

LOREM = (
    "Paragraph one has some sentences. It talks about things.\n\n"
    "Paragraph two is here. It continues the discussion with more words "
    "and even more filler content to make it long enough.\n\n"
    "Paragraph three wraps up. The end."
)


def test_fixed_empty_input() -> None:
    assert FixedSizeChunker(10, 2).chunk("") == []


def test_fixed_short_input_single_chunk() -> None:
    assert FixedSizeChunker(100, 10).chunk("short") == ["short"]


def test_fixed_sizes_and_overlap_invariants() -> None:
    chunker = FixedSizeChunker(20, 5)
    text = "abcdefghij" * 10  # 100 chars
    chunks = chunker.chunk(text)
    assert all(len(c) <= 20 for c in chunks)
    for prev, nxt in pairwise(chunks):
        assert prev[-5:] == nxt[:5]  # exact overlap
    # Reconstruction: strip the 5-char overlap from every chunk after the first.
    rebuilt = chunks[0] + "".join(c[5:] for c in chunks[1:])
    assert rebuilt == text


def test_fixed_no_redundant_tail() -> None:
    chunks = FixedSizeChunker(10, 5).chunk("x" * 10)
    assert chunks == ["x" * 10]


def test_recursive_empty_input() -> None:
    assert RecursiveCharacterChunker(10, 2).chunk("") == []


def test_recursive_respects_max_size() -> None:
    for size, overlap in [(30, 0), (50, 10), (80, 20)]:
        chunks = RecursiveCharacterChunker(size, overlap).chunk(LOREM)
        assert chunks, f"no chunks for size={size}"
        assert all(len(c) <= size for c in chunks)
        assert all(c.strip() for c in chunks)


def test_recursive_prefers_paragraph_boundaries() -> None:
    chunks = RecursiveCharacterChunker(120, 0).chunk(LOREM)
    assert chunks[0].startswith("Paragraph one")


def test_recursive_preserves_all_content_without_overlap() -> None:
    chunks = RecursiveCharacterChunker(40, 0).chunk(LOREM)
    assert "".join(chunks) == LOREM


def test_recursive_hard_cuts_unbreakable_text() -> None:
    text = "a" * 95  # no separators at all
    chunks = RecursiveCharacterChunker(20, 0).chunk(text)
    assert all(len(c) <= 20 for c in chunks)
    assert "".join(chunks) == text


def test_invalid_params_rejected() -> None:
    with pytest.raises(InvalidInputError):
        FixedSizeChunker(0, 0)
    with pytest.raises(InvalidInputError):
        RecursiveCharacterChunker(10, 10)
    with pytest.raises(InvalidInputError):
        build_chunker("semantic", 10, 0)


def test_build_chunker_factory() -> None:
    assert isinstance(build_chunker("fixed", 10, 2), FixedSizeChunker)
    assert isinstance(build_chunker("recursive", 10, 2), RecursiveCharacterChunker)
