"""Tests for embedding providers (fake determinism + mocked Bedrock)."""

import io
import json
import math
from unittest.mock import MagicMock

import pytest

from rag_providers.bedrock import BedrockEmbeddingProvider
from rag_providers.embedding import FakeEmbeddingProvider
from rag_providers.factory import build_embedding_provider


async def test_fake_is_deterministic() -> None:
    provider = FakeEmbeddingProvider()
    [a1], [a2] = await provider.embed(["hello"]), await provider.embed(["hello"])
    assert a1 == a2


async def test_fake_differs_by_text() -> None:
    provider = FakeEmbeddingProvider()
    a, b = await provider.embed(["hello", "world"])
    assert a != b


async def test_fake_dimension_and_norm() -> None:
    provider = FakeEmbeddingProvider(dimension=1024)
    [vec] = await provider.embed(["normalize me"])
    assert len(vec) == 1024
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


def _mock_bedrock_client(embedding: list[float] | None) -> MagicMock:
    client = MagicMock()
    payload = {} if embedding is None else {"embedding": embedding}
    client.invoke_model.return_value = {"body": io.BytesIO(json.dumps(payload).encode())}
    return client


async def test_bedrock_provider_maps_response() -> None:
    client = _mock_bedrock_client([0.1, 0.2, 0.3])
    provider = BedrockEmbeddingProvider(dimension=3, client=client)
    result = await provider.embed(["hi"])
    assert result == [[0.1, 0.2, 0.3]]
    call = client.invoke_model.call_args
    assert call.kwargs["modelId"] == "amazon.titan-embed-text-v2:0"
    body = json.loads(call.kwargs["body"])
    assert body["inputText"] == "hi"
    assert body["dimensions"] == 3
    assert body["normalize"] is True


async def test_bedrock_provider_raises_on_empty() -> None:
    client = _mock_bedrock_client(None)
    provider = BedrockEmbeddingProvider(client=client)
    with pytest.raises(RuntimeError, match="no embedding"):
        await provider.embed(["hi"])
