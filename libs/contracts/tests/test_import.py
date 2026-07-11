"""Smoke test: the contracts package is importable and versioned."""

import rag_contracts


def test_version() -> None:
    assert rag_contracts.__version__
