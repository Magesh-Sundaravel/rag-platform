"""Embedding provider protocol and the deterministic fake."""

import hashlib
import math
import random
from collections.abc import Sequence
from typing import Protocol

DEFAULT_DIMENSION = 1024


class EmbeddingProvider(Protocol):
    """Turns texts into fixed-dimension vectors."""

    dimension: int

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed a batch of texts.

        Args:
            texts: Input strings.

        Returns:
            One ``dimension``-length vector per input, in order.
        """
        ...


class FakeEmbeddingProvider:
    """Deterministic offline embeddings: sha256-seeded unit vectors.

    Vectors carry no semantic meaning; they exist so pipelines, storage, and
    ranking mechanics are fully testable without network access (ADR-0006).
    """

    def __init__(self, dimension: int = DEFAULT_DIMENSION) -> None:
        """Configure the output dimension.

        Args:
            dimension: Vector length (default 1024, matching Bedrock Titan config).
        """
        self.dimension = dimension

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed texts deterministically.

        Args:
            texts: Input strings.

        Returns:
            L2-normalized vectors, stable across processes and runs.
        """
        return [self._vector(text) for text in texts]

    def _vector(self, text: str) -> list[float]:
        """Build one seeded unit vector.

        Args:
            text: Input string.

        Returns:
            The vector for ``text``.
        """
        seed = int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big")
        rng = random.Random(seed)
        values = [rng.gauss(0.0, 1.0) for _ in range(self.dimension)]
        norm = math.sqrt(sum(v * v for v in values)) or 1.0
        return [v / norm for v in values]
