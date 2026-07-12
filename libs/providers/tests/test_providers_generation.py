"""Tests for generation providers (fake determinism + mocked Gemini)."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from rag_providers.factory import build_generation_provider
from rag_providers.gemini import GeminiGenerationProvider
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


def _mock_genai_client(text: str, prompt_tokens: int, completion_tokens: int) -> MagicMock:
    client = MagicMock()
    response = MagicMock()
    response.text = text
    response.usage_metadata.prompt_token_count = prompt_tokens
    response.usage_metadata.candidates_token_count = completion_tokens
    client.aio.models.generate_content = AsyncMock(return_value=response)
    return client


async def test_gemini_provider_maps_response() -> None:
    client = _mock_genai_client("the answer [1]", prompt_tokens=12, completion_tokens=3)
    provider = GeminiGenerationProvider(client=client)
    result = await provider.generate("a prompt")
    assert result.text == "the answer [1]"
    assert result.prompt_tokens == 12
    assert result.completion_tokens == 3
    call = client.aio.models.generate_content.call_args
    assert call.kwargs["model"] == "gemini-2.5-flash"
    assert call.kwargs["contents"] == "a prompt"
