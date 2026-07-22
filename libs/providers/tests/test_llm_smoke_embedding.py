"""Real Bedrock embedding smoke test (llm-smoke workflow only)."""

import os

import pytest

pytestmark = pytest.mark.skipif(
    not (os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")),
    reason="AWS region not set for Bedrock",
)


async def test_real_bedrock_embedding() -> None:
    from rag_providers.bedrock import BedrockEmbeddingProvider

    provider = BedrockEmbeddingProvider()
    [vector] = await provider.embed(["retrieval augmented generation"])
    assert len(vector) == 1024
    assert any(v != 0.0 for v in vector)
