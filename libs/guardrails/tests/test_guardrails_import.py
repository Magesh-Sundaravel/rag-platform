"""Smoke test: the guardrails package is importable and versioned."""

import rag_guardrails


def test_version() -> None:
    assert rag_guardrails.__version__
