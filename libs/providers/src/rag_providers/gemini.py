"""Gemini provider implementations via the google-genai SDK.

Requires ``GEMINI_API_KEY`` in the environment; only exercised by the
llm-smoke workflow and production deployments (ADR-0006).
"""

from collections.abc import Sequence

from google import genai
from google.genai import types

from rag_providers.embedding import DEFAULT_DIMENSION
from rag_providers.generation import GenerationResult

EMBEDDING_MODEL = "gemini-embedding-001"
GENERATION_MODEL = "gemini-2.5-flash"


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


class GeminiGenerationProvider:
    """Answer generation from ``gemini-2.5-flash``."""

    def __init__(
        self,
        model: str = GENERATION_MODEL,
        client: genai.Client | None = None,
    ) -> None:
        """Configure the provider.

        Args:
            model: Gemini generation model name.
            client: Optional pre-built client (tests inject a mock);
                defaults to ``genai.Client()`` which reads ``GEMINI_API_KEY``.
        """
        self.model = model
        self._client = client or genai.Client()

    async def generate(self, prompt: str) -> GenerationResult:
        """Generate an answer via the Gemini API.

        Args:
            prompt: The full grounded prompt (question + numbered context).

        Returns:
            The generated text and token usage.
        """
        response = await self._client.aio.models.generate_content(model=self.model, contents=prompt)
        usage = response.usage_metadata
        return GenerationResult(
            text=response.text or "",
            prompt_tokens=(usage.prompt_token_count or 0) if usage else 0,
            completion_tokens=(usage.candidates_token_count or 0) if usage else 0,
        )
