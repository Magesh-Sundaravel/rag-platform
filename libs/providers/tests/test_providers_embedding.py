"""Tests for embedding providers (fake determinism + mocked Gemini)."""

import math
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from rag_providers.embedding import FakeEmbeddingProvider
from rag_providers.factory import build_embedding_provider
from rag_providers.gemini import GeminiEmbeddingProvider


async def test_fake_is_deterministic() -> None:
    provider = FakeEmbeddingProvider()
    [a1], [a2] = await provider.embed(["hello"]), await provider.embed(["hello"])
    assert a1 == a2


async def test_fake_differs_by_text() -> None:
    provider = FakeEmbeddingProvider()
    a, b = await provider.embed(["hello", "world"])
    assert a != b


async def test_fake_dimension_and_norm() -> None:
    provider = FakeEmbeddingProvider(dimension=768)
    [vec] = await provider.embed(["normalize me"])
    assert len(vec) == 768
    assert math.isclose(math.sqrt(sum(v * v for v in vec)), 1.0, rel_tol=1e-9)


async def test_fake_batch_order_preserved() -> None:
    provider = FakeEmbeddingProvider(dimension=16)
    batch = await provider.embed(["a", "b", "a"])
    assert batch[0] == batch[2]
    assert batch[0] != batch[1]


def test_factory_builds_fake() -> None:
    provider = build_embedding_provider("fake", 32)
    assert isinstance(provider, FakeEmbeddingProvider)
    assert provider.dimension == 32


def test_factory_rejects_unknown() -> None:
    with pytest.raises(ValueError, match="unknown embedding provider"):
        build_embedding_provider("openai")


def _mock_genai_client(embeddings: list[Any]) -> MagicMock:
    client = MagicMock()
    response = MagicMock()
    response.embeddings = embeddings
    client.aio.models.embed_content = AsyncMock(return_value=response)
    return client


async def test_gemini_provider_maps_response() -> None:
    emb = MagicMock()
    emb.values = [0.1, 0.2, 0.3]
    client = _mock_genai_client([emb])
    provider = GeminiEmbeddingProvider(dimension=3, client=client)
    result = await provider.embed(["hi"])
    assert result == [[0.1, 0.2, 0.3]]
    call = client.aio.models.embed_content.call_args
    assert call.kwargs["model"] == "gemini-embedding-001"
    assert call.kwargs["contents"] == ["hi"]
    assert call.kwargs["config"].output_dimensionality == 3


async def test_gemini_provider_raises_on_empty() -> None:
    client = _mock_genai_client([])
    provider = GeminiEmbeddingProvider(client=client)
    with pytest.raises(RuntimeError, match="no embeddings"):
        await provider.embed(["hi"])
