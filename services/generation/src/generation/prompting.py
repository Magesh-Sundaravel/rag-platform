"""Grounded prompt construction and citation extraction."""

import re

from rag_contracts.generation import Citation
from rag_contracts.search import SearchResultItem

_CITATION_MARKER = re.compile(r"\[(\d+)\]")
_SNIPPET_LENGTH = 200


def build_prompt(question: str, chunks: list[SearchResultItem]) -> str:
    """Build a grounded prompt with numbered context blocks.

    Args:
        question: The user's question.
        chunks: Retrieved chunks to ground the answer in, best-first.

    Returns:
        A prompt instructing the model to answer using only the numbered
        context and to cite sources with bracket references like ``[1]``.
    """
    context = "\n".join(f"[{i}] {chunk.text}" for i, chunk in enumerate(chunks, start=1))
    return (
        "Answer the question using only the numbered context below. "
        "Cite sources inline using bracket references like [1].\n\n"
        f"{context}\n\n"
        f"Question: {question}"
    )


def extract_citations(answer: str, chunks: list[SearchResultItem]) -> list[Citation]:
    """Map ``[n]`` markers in the answer to their source chunks.

    Args:
        answer: The generated answer text.
        chunks: The chunks the prompt was built from, in the same order
            used to number them (1-indexed).

    Returns:
        Citations in order of first appearance in the answer, deduplicated.
    """
    seen: set[int] = set()
    citations: list[Citation] = []
    for match in _CITATION_MARKER.finditer(answer):
        n = int(match.group(1))
        if n in seen or not (1 <= n <= len(chunks)):
            continue
        seen.add(n)
        chunk = chunks[n - 1]
        citations.append(
            Citation(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                snippet=chunk.text[:_SNIPPET_LENGTH],
            )
        )
    return citations
