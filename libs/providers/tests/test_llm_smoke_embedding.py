"""Real Gemini embedding smoke test (llm-smoke workflow only)."""

import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("GEMINI_API_KEY"), reason="GEMINI_API_KEY not set"
)


async def test_real_gemini_embedding() -> None:
    from rag_providers.gemini import GeminiEmbeddingProvider

    provider = GeminiEmbeddingProvider()
    [vector] = await provider.embed(["retrieval augmented generation"])
    assert len(vector) == 768
    assert any(v != 0.0 for v in vector)
