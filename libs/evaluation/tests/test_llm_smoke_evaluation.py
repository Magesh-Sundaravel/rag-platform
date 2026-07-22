"""Real Bedrock-judge evaluation smoke test (llm-smoke workflow only)."""

import os

import pytest

pytestmark = pytest.mark.skipif(
    not (os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")),
    reason="AWS region not set for Bedrock",
)


async def test_real_bedrock_evaluation() -> None:
    from rag_evaluation.golden import GOLDEN_EXAMPLES
    from rag_evaluation.runner import evaluate
    from rag_providers.bedrock import BedrockGenerationProvider

    judge = BedrockGenerationProvider()
    report = await evaluate(GOLDEN_EXAMPLES, judge)

    for result in report.results:
        for score in result.scores.model_dump().values():
            assert 0.0 <= score <= 1.0

    supported, hallucinated, _ = report.results
    assert supported.scores.faithfulness > hallucinated.scores.faithfulness
