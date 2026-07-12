"""Judge-prompted scoring: turn a free-text judge response into a float score."""

import re

from rag_providers.generation import GenerationProvider

SCORE_INSTRUCTION = (
    "Respond with only a number between 0.0 and 1.0 on the first line, "
    "with no other text before it."
)
_SCORE_PATTERN = re.compile(r"(-?\d*\.?\d+)")


async def score_from_judge(prompt: str, judge: GenerationProvider) -> float:
    """Prompt the judge and parse a ``[0.0, 1.0]`` score from its response.

    Args:
        prompt: The full judge prompt (should end with the score
            instruction; see ``SCORE_INSTRUCTION``).
        judge: The generation provider acting as judge.

    Returns:
        The first number found in the response, clamped to ``[0.0, 1.0]``.
        Returns ``0.0`` if the response contains no number.
    """
    result = await judge.generate(prompt)
    match = _SCORE_PATTERN.search(result.text)
    if not match:
        return 0.0
    return max(0.0, min(1.0, float(match.group(1))))
