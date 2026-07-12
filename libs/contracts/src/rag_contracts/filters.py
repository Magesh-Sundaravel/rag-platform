"""Metadata filter contracts used by retrieval queries."""

from enum import StrEnum

from pydantic import BaseModel, model_validator


class FilterOp(StrEnum):
    """Supported filter operators."""

    EQ = "eq"
    IN = "in"


class MetadataFilter(BaseModel):
    """A single constraint on chunk metadata (AND-combined by callers).

    ``eq`` compares a metadata key to one string; ``in`` matches any of a
    non-empty list of strings.
    """

    field: str
    op: FilterOp = FilterOp.EQ
    value: str | list[str]

    @model_validator(mode="after")
    def _check_value_matches_op(self) -> "MetadataFilter":
        """Validate the value shape for the chosen operator."""
        if self.op is FilterOp.EQ and not isinstance(self.value, str):
            raise ValueError("op 'eq' requires a string value")
        if self.op is FilterOp.IN and (not isinstance(self.value, list) or not self.value):
            raise ValueError("op 'in' requires a non-empty list of strings")
        return self
