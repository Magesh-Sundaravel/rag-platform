"""Tests for the four RAGAS-style metric functions."""

from collections.abc import Callable

from rag_evaluation.metrics import answer_relevancy, context_precision, context_recall, faithfulness
from rag_providers.generation import GenerationProvider


async def test_faithfulness_scores_and_prompts_with_context(
    make_judge: Callable[[str], GenerationProvider],
) -> None:
    judge = make_judge("0.9")
    score = await faithfulness("Paris is the capital.", ["Paris is the capital of France."], judge)
    assert score == 0.9


async def test_answer_relevancy_scores(make_judge: Callable[[str], GenerationProvider]) -> None:
    judge = make_judge("0.8")
    score = await answer_relevancy("what is the capital?", "Paris.", judge)
    assert score == 0.8


async def test_context_precision_scores(make_judge: Callable[[str], GenerationProvider]) -> None:
    judge = make_judge("0.7")
    score = await context_precision("what is the capital?", ["Paris is the capital."], judge)
    assert score == 0.7


async def test_context_recall_scores(make_judge: Callable[[str], GenerationProvider]) -> None:
    judge = make_judge("0.6")
    contexts = ["Paris is the capital."]
    score = await context_recall(contexts, "Paris is the capital of France.", judge)
    assert score == 0.6
