"""Real Gemini-judge evaluation smoke test (llm-smoke workflow only)."""

import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("GEMINI_API_KEY"), reason="GEMINI_API_KEY not set"
)


async def test_real_gemini_evaluation() -> None:
    from rag_evaluation.golden import GOLDEN_EXAMPLES
    from rag_evaluation.runner import evaluate
    from rag_providers.gemini import GeminiGenerationProvider

    judge = GeminiGenerationProvider()
    report = await evaluate(GOLDEN_EXAMPLES, judge)

    for result in report.results:
        for score in result.scores.model_dump().values():
            assert 0.0 <= score <= 1.0

    supported, hallucinated, _ = report.results
    assert supported.scores.faithfulness > hallucinated.scores.faithfulness
