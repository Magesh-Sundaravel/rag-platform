"""Gemini provider implementations via the google-genai SDK.

Requires ``GEMINI_API_KEY`` in the environment; only exercised by the
llm-smoke workflow and production deployments (ADR-0006).
"""

from collections.abc import Sequence

from google import genai
from google.genai import types

from rag_providers.embedding import DEFAULT_DIMENSION

EMBEDDING_MODEL = "gemini-embedding-001"


class GeminiEmbeddingProvider:
    """Embeddings from ``gemini-embedding-001`` (768 dims by default)."""

    def __init__(
        self,
        model: str = EMBEDDING_MODEL,
        dimension: int = DEFAULT_DIMENSION,
        client: genai.Client | None = None,
    ) -> None:
        """Configure the provider.

        Args:
            model: Gemini embedding model name.
            dimension: Output dimensionality requested from the API.
            client: Optional pre-built client (tests inject a mock);
                defaults to ``genai.Client()`` which reads ``GEMINI_API_KEY``.
        """
        self.model = model
        self.dimension = dimension
        self._client = client or genai.Client()

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed a batch of texts via the Gemini API.

        Args:
            texts: Input strings.

        Returns:
            One vector per input, in order.

        Raises:
            RuntimeError: If the API returns no embeddings.
        """
        response = await self._client.aio.models.embed_content(
            model=self.model,
            contents=list(texts),
            config=types.EmbedContentConfig(output_dimensionality=self.dimension),
        )
        if not response.embeddings:
            raise RuntimeError("Gemini returned no embeddings")
        return [list(e.values or []) for e in response.embeddings]
