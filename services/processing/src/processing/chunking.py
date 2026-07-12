"""Chunking strategies (own implementation, no LangChain dependency).

Two strategies ship in the MVP: fixed-size character windows and a
recursive character splitter honoring natural boundaries. Semantic and
parent-child chunking are documented future work (Phase 3 spec).
"""

from typing import Literal, Protocol

from rag_common.exceptions import InvalidInputError

ChunkStrategy = Literal["fixed", "recursive"]


class Chunker(Protocol):
    """Strategy interface: split text into retrieval-sized chunks."""

    def chunk(self, text: str) -> list[str]:
        """Split ``text`` into chunks.

        Args:
            text: Input text.

        Returns:
            Non-empty chunks, each at most the configured size.
        """
        ...


def _validate(chunk_size: int, overlap: int) -> None:
    """Validate chunker construction parameters.

    Args:
        chunk_size: Maximum chunk length in characters.
        overlap: Characters shared between consecutive chunks.

    Raises:
        InvalidInputError: If sizes are non-positive or overlap >= size.
    """
    if chunk_size <= 0:
        raise InvalidInputError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise InvalidInputError("overlap must satisfy 0 <= overlap < chunk_size")


class FixedSizeChunker:
    """Sliding character windows of ``chunk_size`` with ``overlap``."""

    def __init__(self, chunk_size: int, overlap: int) -> None:
        """Configure the window.

        Args:
            chunk_size: Maximum chunk length in characters.
            overlap: Characters shared between consecutive chunks.
        """
        _validate(chunk_size, overlap)
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        """Split ``text`` into overlapping fixed-size windows.

        Args:
            text: Input text.

        Returns:
            Chunks of at most ``chunk_size`` characters.
        """
        if not text:
            return []
        step = self.chunk_size - self.overlap
        chunks = []
        for start in range(0, len(text), step):
            piece = text[start : start + self.chunk_size]
            chunks.append(piece)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class RecursiveCharacterChunker:
    """Split on a separator hierarchy, merging pieces up to ``chunk_size``."""

    separators = ("\n\n", "\n", ". ", " ")

    def __init__(self, chunk_size: int, overlap: int) -> None:
        """Configure the splitter.

        Args:
            chunk_size: Maximum chunk length in characters.
            overlap: Characters of the previous chunk prefixed to the next.
        """
        _validate(chunk_size, overlap)
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        """Split ``text`` recursively and merge with overlap.

        Args:
            text: Input text.

        Returns:
            Chunks of at most ``chunk_size`` characters.
        """
        if not text:
            return []
        pieces = self._split(text, 0)
        return self._merge(pieces)

    def _split(self, text: str, level: int) -> list[str]:
        """Recursively split ``text`` so every piece fits ``chunk_size``.

        Args:
            text: Text to split.
            level: Index into the separator hierarchy.

        Returns:
            Pieces each at most ``chunk_size`` characters.
        """
        if len(text) <= self.chunk_size:
            return [text] if text else []
        if level >= len(self.separators):
            return [text[i : i + self.chunk_size] for i in range(0, len(text), self.chunk_size)]
        sep = self.separators[level]
        parts = text.split(sep)
        pieces: list[str] = []
        for i, part in enumerate(parts):
            fragment = part + (sep if i < len(parts) - 1 else "")
            if not fragment:
                continue
            if len(fragment) <= self.chunk_size:
                pieces.append(fragment)
            else:
                pieces.extend(self._split(fragment, level + 1))
        return pieces

    def _merge(self, pieces: list[str]) -> list[str]:
        """Greedily merge pieces into chunks, carrying overlap forward.

        Args:
            pieces: Split fragments, each at most ``chunk_size``.

        Returns:
            Final chunks.
        """
        chunks: list[str] = []
        current = ""
        for piece in pieces:
            if current and len(current) + len(piece) > self.chunk_size:
                chunks.append(current)
                tail = current[-self.overlap :] if self.overlap else ""
                current = tail if len(tail) + len(piece) <= self.chunk_size else ""
            current += piece
        if current.strip():
            chunks.append(current)
        return [c for c in chunks if c.strip()]


def build_chunker(strategy: str, chunk_size: int, overlap: int) -> Chunker:
    """Build the configured chunking strategy.

    Args:
        strategy: ``"fixed"`` or ``"recursive"``.
        chunk_size: Maximum chunk length in characters.
        overlap: Overlap between consecutive chunks.

    Returns:
        A :class:`Chunker` instance.

    Raises:
        InvalidInputError: For an unknown strategy name.
    """
    if strategy == "fixed":
        return FixedSizeChunker(chunk_size, overlap)
    if strategy == "recursive":
        return RecursiveCharacterChunker(chunk_size, overlap)
    raise InvalidInputError(f"unknown chunk strategy: {strategy}")
