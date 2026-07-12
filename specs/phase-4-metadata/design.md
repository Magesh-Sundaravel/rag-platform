# Phase 4 Design

## Contracts (`rag_contracts.filters`)

```python
class FilterOp(StrEnum):
    EQ = "eq"
    IN = "in"

class MetadataFilter(BaseModel):
    field: str          # metadata key, e.g. "language"
    op: FilterOp = EQ
    value: str | list[str]
```

Pydantic model validator: `eq` requires a string value, `in` requires a
non-empty list of strings.

## Predicate translation (`retrieval/filters.py`)

`metadata_predicates(filters) -> list[ColumnElement[bool]]` using
`Chunk.meta[field].as_string()` (portable across Postgres JSONB and SQLite
JSON), `== value` or `.in_(values)`. Callers AND them into any select over
chunks.

## Migration 0003

`CREATE INDEX ix_chunks_metadata_gin ON chunks USING gin (metadata jsonb_path_ops)`
(alembic `op.create_index(..., postgresql_using="gin", postgresql_ops=...)`).

## Tasks

1. Contracts filter model + validation tests.
2. `retrieval/filters.py` + SQLite predicate tests (seed chunks, filter).
3. Migration 0003; CI integration keeps passing.
4. Docs/status; gates; commit; push.
