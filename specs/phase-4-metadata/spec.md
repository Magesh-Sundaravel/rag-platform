# Phase 4 Specification: Metadata Architecture

- **Status:** Accepted
- **Date:** 2026-07-12
- **Phase:** 4 of 10

## Problem

Chunk metadata (Phase 3: title, language, filename) must be queryable so
retrieval can constrain search by document attributes.

## Scope

1. **Schema documentation**: chunk `metadata` JSONB carries flat string
   values; current keys: `title`, `language`, `filename`. New keys may be
   added without migration (JSONB is schemaless); the *contract* documents
   known keys.
2. **GIN index** on `chunks.metadata` (`jsonb_path_ops`) — migration 0003 —
   so equality/containment filters scale.
3. **Filter model** in `rag_contracts.filters`:
   - `MetadataFilter(field, op, value)` with `op ∈ {"eq", "in"}`;
     `value: str | list[str]` validated per op.
4. **Query application**: `retrieval/filters.py` translates a list of
   filters into SQLAlchemy predicates over the JSONB column (AND semantics);
   used by Phase 6 search queries.

## Non-Goals

- Range/negation operators, nested paths (future work).
- Filtering at the documents level (chunk metadata denormalizes what search needs).

## Acceptance Criteria

- [ ] Filter model validates op/value combinations (unit tests).
- [ ] Predicates behave on SQLite (portable JSON accessor) and on Postgres in CI.
- [ ] Migration 0003 creates the GIN index. Gates green.
