"""Tests for the evaluation contracts."""

from rag_contracts.evaluation import EvalExample, EvalResult, EvaluationReport, MetricScores


def test_eval_example_round_trip() -> None:
    example = EvalExample(
        question="what is RAG?",
        contexts=["RAG combines retrieval and generation."],
        answer="RAG is retrieval-augmented generation.",
        ground_truth="RAG combines retrieval and generation.",
    )
    assert example.contexts == ["RAG combines retrieval and generation."]


def test_evaluation_report_round_trip() -> None:
    example = EvalExample(question="q", contexts=["c"], answer="a", ground_truth="g")
    scores = MetricScores(
        faithfulness=0.9, answer_relevancy=0.8, context_precision=0.7, context_recall=0.6
    )
    report = EvaluationReport(results=[EvalResult(example=example, scores=scores)], averages=scores)
    assert report.averages.faithfulness == 0.9
    assert report.results[0].example.question == "q"
