"""Tests for generation providers (fake determinism + mocked Bedrock)."""

from unittest.mock import MagicMock

import pytest

from rag_providers.factory import build_generation_provider
from rag_providers.bedrock import BedrockGenerationProvider
from rag_providers.generation import FakeGenerationProvider


async def test_fake_cites_all_context_blocks() -> None:
    provider = FakeGenerationProvider()
    prompt = "Question: what?\n\n[1] first chunk text\n[2] second chunk text"
    result = await provider.generate(prompt)
    assert result.text == "Based on the provided context [1][2]: first chunk text"


async def test_fake_no_context_blocks() -> None:
    provider = FakeGenerationProvider()
    result = await provider.generate("Question: what?\n\nno context here")
    assert result.text == "I don't have any context to answer this question."


async def test_fake_token_counts_are_word_counts() -> None:
    provider = FakeGenerationProvider()
    prompt = "[1] a b c"
    result = await provider.generate(prompt)
    assert result.prompt_tokens == len(prompt.split())
    assert result.completion_tokens == len(result.text.split())


def test_factory_builds_fake() -> None:
    provider = build_generation_provider("fake")
    assert isinstance(provider, FakeGenerationProvider)


def test_factory_rejects_unknown() -> None:
    with pytest.raises(ValueError, match="unknown generation provider"):
        build_generation_provider("openai")


def _mock_bedrock_client(text: str, prompt_tokens: int, completion_tokens: int) -> MagicMock:
    client = MagicMock()
    client.converse.return_value = {
        "output": {"message": {"content": [{"text": text}]}},
        "usage": {"inputTokens": prompt_tokens, "outputTokens": completion_tokens},
    }
    return client


async def test_bedrock_provider_maps_response() -> None:
    client = _mock_bedrock_client("the answer [1]", prompt_tokens=12, completion_tokens=3)
    provider = BedrockGenerationProvider(client=client)
    result = await provider.generate("a prompt")
    assert result.text == "the answer [1]"
    assert result.prompt_tokens == 12
    assert result.completion_tokens == 3
    call = client.converse.call_args
    assert call.kwargs["modelId"] == "amazon.nova-micro-v1:0"
    assert call.kwargs["messages"] == [{"role": "user", "content": [{"text": "a prompt"}]}]
