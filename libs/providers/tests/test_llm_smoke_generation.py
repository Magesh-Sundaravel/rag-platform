"""Real Gemini generation smoke test (llm-smoke workflow only)."""

import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("GEMINI_API_KEY"), reason="GEMINI_API_KEY not set"
)


async def test_real_gemini_generation() -> None:
    from rag_providers.gemini import GeminiGenerationProvider

    provider = GeminiGenerationProvider()
    prompt = "[1] Paris is the capital of France.\n\nQuestion: what is the capital of France?"
    result = await provider.generate(prompt)
    assert result.text
    assert result.prompt_tokens > 0
