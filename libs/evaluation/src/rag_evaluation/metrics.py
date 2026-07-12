"""The four core RAGAS-style metrics, each scored by a judge prompt."""

from rag_evaluation.judging import SCORE_INSTRUCTION, score_from_judge
from rag_providers.generation import GenerationProvider


async def faithfulness(answer: str, contexts: list[str], judge: GenerationProvider) -> float:
    """Score how well ``answer`` is supported by ``contexts``.

    Args:
        answer: The generated answer.
        contexts: The retrieved context chunks it was grounded in.
        judge: The generation provider acting as judge.

    Returns:
        A faithfulness score in ``[0.0, 1.0]``.
    """
    context_block = "\n".join(f"- {c}" for c in contexts)
    prompt = (
        "Context:\n"
        f"{context_block}\n\n"
        f"Answer: {answer}\n\n"
        "How fully is every claim in the answer supported by the context above? "
        f"1.0 means fully supported, 0.0 means unsupported or contradicted. {SCORE_INSTRUCTION}"
    )
    return await score_from_judge(prompt, judge)


async def answer_relevancy(question: str, answer: str, judge: GenerationProvider) -> float:
    """Score how directly ``answer`` addresses ``question``.

    Args:
        question: The original question.
        answer: The generated answer.
        judge: The generation provider acting as judge.

    Returns:
        An answer-relevancy score in ``[0.0, 1.0]``.
    """
    prompt = (
        f"Question: {question}\n\n"
        f"Answer: {answer}\n\n"
        "How directly and completely does the answer address the question? "
        f"1.0 means fully relevant, 0.0 means irrelevant. {SCORE_INSTRUCTION}"
    )
    return await score_from_judge(prompt, judge)


async def context_precision(question: str, contexts: list[str], judge: GenerationProvider) -> float:
    """Score how relevant the retrieved ``contexts`` are to ``question``.

    Args:
        question: The original question.
        contexts: The retrieved context chunks.
        judge: The generation provider acting as judge.

    Returns:
        A context-precision score in ``[0.0, 1.0]``.
    """
    context_block = "\n".join(f"- {c}" for c in contexts)
    prompt = (
        f"Question: {question}\n\n"
        f"Retrieved context:\n{context_block}\n\n"
        "What fraction of the retrieved context is actually relevant to answering "
        f"the question? 1.0 means all of it is relevant. {SCORE_INSTRUCTION}"
    )
    return await score_from_judge(prompt, judge)


async def context_recall(
    contexts: list[str], ground_truth: str, judge: GenerationProvider
) -> float:
    """Score how much of ``ground_truth`` is covered by the retrieved ``contexts``.

    Args:
        contexts: The retrieved context chunks.
        ground_truth: The expected (reference) answer.
        judge: The generation provider acting as judge.

    Returns:
        A context-recall score in ``[0.0, 1.0]``.
    """
    context_block = "\n".join(f"- {c}" for c in contexts)
    prompt = (
        f"Ground-truth answer: {ground_truth}\n\n"
        f"Retrieved context:\n{context_block}\n\n"
        "What fraction of the ground-truth answer's content can be attributed to "
        f"the retrieved context? 1.0 means all of it is covered. {SCORE_INSTRUCTION}"
    )
    return await score_from_judge(prompt, judge)
