"""Tests for judge-response score parsing."""

from collections.abc import Callable

from rag_evaluation.judging import score_from_judge
from rag_providers.generation import GenerationProvider


async def test_parses_well_formed_score(make_judge: Callable[[str], GenerationProvider]) -> None:
    score = await score_from_judge("prompt", make_judge("0.75"))
    assert score == 0.75


async def test_parses_score_with_surrounding_text(
    make_judge: Callable[[str], GenerationProvider],
) -> None:
    score = await score_from_judge("prompt", make_judge("0.4\nreason: partially supported"))
    assert score == 0.4


async def test_clamps_above_one(make_judge: Callable[[str], GenerationProvider]) -> None:
    score = await score_from_judge("prompt", make_judge("1.5"))
    assert score == 1.0


async def test_clamps_below_zero(make_judge: Callable[[str], GenerationProvider]) -> None:
    score = await score_from_judge("prompt", make_judge("-0.5"))
    assert score == 0.0


async def test_malformed_response_defaults_to_zero(
    make_judge: Callable[[str], GenerationProvider],
) -> None:
    score = await score_from_judge("prompt", make_judge("I cannot answer that."))
    assert score == 0.0
