"""Smoke test: the evaluation package is importable and versioned."""

import rag_evaluation


def test_version() -> None:
    assert rag_evaluation.__version__
