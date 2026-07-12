"""Generation provider protocol and the deterministic fake."""

import re
from dataclasses import dataclass
from typing import Protocol

_CONTEXT_LINE = re.compile(r"^\[(\d+)\] (.*)$", re.MULTILINE)


@dataclass
class GenerationResult:
    """The text and token usage produced by a generation call."""

    text: str
    prompt_tokens: int
    completion_tokens: int


class GenerationProvider(Protocol):
    """Turns a grounded prompt into an answer."""

    async def generate(self, prompt: str) -> GenerationResult:
        """Generate an answer for a prompt.

        Args:
            prompt: The full grounded prompt (question + numbered context).

        Returns:
            The generated text and token usage.
        """
        ...


class FakeGenerationProvider:
    """Deterministic offline generation: echoes the numbered context ids.

    Finds ``[n] <text>`` context blocks in the prompt and answers with the
    first block's text, citing every block id it saw. This makes citation
    extraction fully testable offline (ADR-0006).
    """

    async def generate(self, prompt: str) -> GenerationResult:
        """Generate a deterministic answer from the prompt's context blocks.

        Args:
            prompt: The full grounded prompt (question + numbered context).

        Returns:
            An answer citing every context block id found, plus word-count
            token usage.
        """
        matches = _CONTEXT_LINE.findall(prompt)
        if not matches:
            text = "I don't have any context to answer this question."
        else:
            citations = "".join(f"[{n}]" for n, _ in matches)
            first_line = matches[0][1]
            text = f"Based on the provided context {citations}: {first_line}"
        return GenerationResult(
            text=text,
            prompt_tokens=len(prompt.split()),
            completion_tokens=len(text.split()),
        )
