"""Real Bedrock generation smoke test (llm-smoke workflow only)."""

import os

import pytest

pytestmark = pytest.mark.skipif(
    not (os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")),
    reason="AWS region not set for Bedrock",
)


async def test_real_bedrock_generation() -> None:
    from rag_providers.bedrock import BedrockGenerationProvider

    provider = BedrockGenerationProvider()
    prompt = "[1] Paris is the capital of France.\n\nQuestion: what is the capital of France?"
    result = await provider.generate(prompt)
    assert result.text
    assert result.prompt_tokens > 0
