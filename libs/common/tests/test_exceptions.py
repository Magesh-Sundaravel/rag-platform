"""Tests for the rag_common exception hierarchy."""

import pytest

from rag_common.exceptions import (
    ConflictError,
    InvalidInputError,
    NotFoundError,
    RagPlatformError,
    UpstreamError,
)


@pytest.mark.parametrize(
    ("exc_cls", "expected_code", "expected_status"),
    [
        (NotFoundError, "not_found", 404),
        (InvalidInputError, "invalid_input", 422),
        (ConflictError, "conflict", 409),
        (UpstreamError, "upstream_error", 502),
    ],
)
def test_subclasses_carry_code_and_status(
    exc_cls: type[RagPlatformError], expected_code: str, expected_status: int
) -> None:
    exc = exc_cls("boom")
    assert isinstance(exc, RagPlatformError)
    assert exc.code == expected_code
    assert exc.status_code == expected_status
    assert exc.detail == "boom"
    assert str(exc) == "boom"


def test_base_error_defaults() -> None:
    exc = RagPlatformError("generic failure")
    assert exc.code == "internal_error"
    assert exc.status_code == 500
