"""Config-driven provider construction."""

from rag_providers.embedding import DEFAULT_DIMENSION, EmbeddingProvider, FakeEmbeddingProvider
from rag_providers.generation import FakeGenerationProvider, GenerationProvider


def build_embedding_provider(name: str, dimension: int = DEFAULT_DIMENSION) -> EmbeddingProvider:
    """Build an embedding provider by name.

    Args:
        name: ``"fake"`` or ``"bedrock"``.
        dimension: Vector dimension.

    Returns:
        A configured provider.

    Raises:
        ValueError: For an unknown provider name.
    """
    if name == "fake":
        return FakeEmbeddingProvider(dimension)
    if name == "bedrock":
        from rag_providers.bedrock import BedrockEmbeddingProvider

        return BedrockEmbeddingProvider(dimension=dimension)
    raise ValueError(f"unknown embedding provider: {name}")


def build_generation_provider(name: str) -> GenerationProvider:
    """Build a generation provider by name.

    Args:
        name: ``"fake"`` or ``"bedrock"``.

    Returns:
        A configured provider.

    Raises:
        ValueError: For an unknown provider name.
    """
    if name == "fake":
        return FakeGenerationProvider()
    if name == "bedrock":
        from rag_providers.bedrock import BedrockGenerationProvider

        return BedrockGenerationProvider()
    raise ValueError(f"unknown generation provider: {name}")
