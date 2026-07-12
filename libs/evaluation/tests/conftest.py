"""Shared test fixtures for rag_evaluation tests."""

from collections.abc import Callable

import pytest

from rag_providers.generation import GenerationProvider, GenerationResult


class StubJudge:
    """A judge double returning a canned response, for deterministic tests."""

    def __init__(self, response_text: str) -> None:
        self.response_text = response_text
        self.prompts: list[str] = []

    async def generate(self, prompt: str) -> GenerationResult:
        self.prompts.append(prompt)
        return GenerationResult(text=self.response_text, prompt_tokens=0, completion_tokens=0)


@pytest.fixture
def make_judge() -> Callable[[str], GenerationProvider]:
    """Return a factory for building a ``StubJudge`` with a given response."""
    return StubJudge
