"""Contracts for RAGAS-style evaluation of retrieval-augmented answers."""

from pydantic import BaseModel


class EvalExample(BaseModel):
    """One golden example: question, retrieved contexts, answer, and ground truth."""

    question: str
    contexts: list[str]
    answer: str
    ground_truth: str


class MetricScores(BaseModel):
    """The four core RAGAS metrics, each in ``[0.0, 1.0]``."""

    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float


class EvalResult(BaseModel):
    """The scores for one evaluated example."""

    example: EvalExample
    scores: MetricScores


class EvaluationReport(BaseModel):
    """Per-example results plus dataset-wide metric averages."""

    results: list[EvalResult]
    averages: MetricScores
