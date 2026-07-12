"""Tests for evaluate() aggregation over the golden dataset shape."""

from collections.abc import Callable

import pytest

from rag_contracts.evaluation import EvalExample
from rag_evaluation.golden import GOLDEN_EXAMPLES
from rag_evaluation.runner import evaluate
from rag_providers.generation import GenerationProvider


def test_golden_dataset_has_three_examples() -> None:
    assert len(GOLDEN_EXAMPLES) == 3


async def test_evaluate_scores_every_example(
    make_judge: Callable[[str], GenerationProvider],
) -> None:
    report = await evaluate(GOLDEN_EXAMPLES, make_judge("0.5"))
    assert len(report.results) == 3
    assert all(r.scores.faithfulness == 0.5 for r in report.results)


async def test_evaluate_averages_scores(make_judge: Callable[[str], GenerationProvider]) -> None:
    report = await evaluate(GOLDEN_EXAMPLES, make_judge("0.5"))
    assert report.averages.faithfulness == 0.5
    assert report.averages.answer_relevancy == 0.5
    assert report.averages.context_precision == 0.5
    assert report.averages.context_recall == 0.5


async def test_evaluate_rejects_empty_dataset(
    make_judge: Callable[[str], GenerationProvider],
) -> None:
    with pytest.raises(ValueError, match="at least one example"):
        await evaluate([], make_judge("0.5"))


async def test_evaluate_preserves_example_order(
    make_judge: Callable[[str], GenerationProvider],
) -> None:
    examples = [
        EvalExample(question="q1", contexts=["c1"], answer="a1", ground_truth="g1"),
        EvalExample(question="q2", contexts=["c2"], answer="a2", ground_truth="g2"),
    ]
    report = await evaluate(examples, make_judge("0.5"))
    assert [r.example.question for r in report.results] == ["q1", "q2"]
