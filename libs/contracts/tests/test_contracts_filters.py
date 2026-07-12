"""Tests for the metadata filter contract model."""

import pytest
from pydantic import ValidationError

from rag_contracts.filters import FilterOp, MetadataFilter


def test_eq_filter_valid() -> None:
    f = MetadataFilter(field="language", value="en")
    assert f.op is FilterOp.EQ
    assert f.value == "en"


def test_in_filter_valid() -> None:
    f = MetadataFilter(field="filename", op=FilterOp.IN, value=["a.txt", "b.txt"])
    assert f.op is FilterOp.IN


def test_eq_rejects_list() -> None:
    with pytest.raises(ValidationError, match="eq"):
        MetadataFilter(field="language", op=FilterOp.EQ, value=["en"])


def test_in_rejects_string_and_empty_list() -> None:
    with pytest.raises(ValidationError, match="in"):
        MetadataFilter(field="language", op=FilterOp.IN, value="en")
    with pytest.raises(ValidationError, match="in"):
        MetadataFilter(field="language", op=FilterOp.IN, value=[])


def test_unknown_op_rejected() -> None:
    with pytest.raises(ValidationError):
        MetadataFilter.model_validate({"field": "language", "op": "gt", "value": "en"})
