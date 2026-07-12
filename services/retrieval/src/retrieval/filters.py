"""Translate metadata filter contracts into SQLAlchemy predicates."""

from sqlalchemy import ColumnElement

from rag_contracts.filters import FilterOp, MetadataFilter
from rag_db.models import Chunk


def metadata_predicates(filters: list[MetadataFilter]) -> list[ColumnElement[bool]]:
    """Build AND-able predicates over the chunk JSONB metadata column.

    Uses the portable JSON string accessor so the same predicates run on
    Postgres (JSONB) in production and SQLite (JSON) in unit tests.

    Args:
        filters: Validated metadata filters.

    Returns:
        One boolean SQL expression per filter.
    """
    predicates: list[ColumnElement[bool]] = []
    for f in filters:
        accessor = Chunk.meta[f.field].as_string()
        if f.op is FilterOp.EQ:
            predicates.append(accessor == f.value)
        else:
            values = f.value if isinstance(f.value, list) else [f.value]
            predicates.append(accessor.in_(values))
    return predicates
