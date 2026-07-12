"""A tiny, fixed golden dataset shared by the unit test and the llm-smoke test.

Covers: a fully supported answer, a hallucinated (unsupported) answer, and
an irrelevant-context case.
"""

from rag_contracts.evaluation import EvalExample

GOLDEN_EXAMPLES: list[EvalExample] = [
    EvalExample(
        question="What is the capital of France?",
        contexts=["Paris is the capital and most populous city of France."],
        answer="Paris is the capital of France.",
        ground_truth="Paris is the capital of France.",
    ),
    EvalExample(
        question="What is the capital of France?",
        contexts=["Paris is the capital and most populous city of France."],
        answer="The capital of France is Paris, which has a population of 50 million.",
        ground_truth="Paris is the capital of France.",
    ),
    EvalExample(
        question="What is the capital of France?",
        contexts=["The Eiffel Tower was completed in 1889 for the World's Fair."],
        answer="The Eiffel Tower is a famous landmark in Paris.",
        ground_truth="Paris is the capital of France.",
    ),
]
