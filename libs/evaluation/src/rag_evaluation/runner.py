"""Runs the four RAGAS-style metrics over a dataset and averages the scores."""

import asyncio

from rag_contracts.evaluation import EvalExample, EvalResult, EvaluationReport, MetricScores
from rag_evaluation.metrics import answer_relevancy, context_precision, context_recall, faithfulness
from rag_providers.generation import GenerationProvider


async def _score_example(example: EvalExample, judge: GenerationProvider) -> MetricScores:
    """Score one example on all four metrics, concurrently.

    Args:
        example: The example to score.
        judge: The generation provider acting as judge.

    Returns:
        The four metric scores for this example.
    """
    faithfulness_score, relevancy_score, precision_score, recall_score = await asyncio.gather(
        faithfulness(example.answer, example.contexts, judge),
        answer_relevancy(example.question, example.answer, judge),
        context_precision(example.question, example.contexts, judge),
        context_recall(example.contexts, example.ground_truth, judge),
    )
    return MetricScores(
        faithfulness=faithfulness_score,
        answer_relevancy=relevancy_score,
        context_precision=precision_score,
        context_recall=recall_score,
    )


def _average(all_scores: list[MetricScores]) -> MetricScores:
    """Average each metric across a list of per-example scores."""
    n = len(all_scores)
    return MetricScores(
        faithfulness=sum(s.faithfulness for s in all_scores) / n,
        answer_relevancy=sum(s.answer_relevancy for s in all_scores) / n,
        context_precision=sum(s.context_precision for s in all_scores) / n,
        context_recall=sum(s.context_recall for s in all_scores) / n,
    )


async def evaluate(examples: list[EvalExample], judge: GenerationProvider) -> EvaluationReport:
    """Score every example on all four metrics and average the results.

    Args:
        examples: The dataset to evaluate.
        judge: The generation provider acting as judge.

    Returns:
        Per-example results plus dataset-wide metric averages.

    Raises:
        ValueError: If ``examples`` is empty.
    """
    if not examples:
        raise ValueError("evaluate() requires at least one example")
    all_scores = await asyncio.gather(*(_score_example(ex, judge) for ex in examples))
    results = [EvalResult(example=ex, scores=s) for ex, s in zip(examples, all_scores, strict=True)]
    return EvaluationReport(results=results, averages=_average(all_scores))
