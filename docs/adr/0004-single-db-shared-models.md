# ADR-0004: Single shared database with shared ORM models

- **Status:** Accepted
- **Date:** 2026-07-12

## Context

The MVP runs one Postgres instance (docker-compose, later Cloud SQL). The
ingestion, processing, and retrieval services all read/write the same
`documents`/`jobs`/`chunks` data. Per-service databases would force
cross-service APIs (or event streams) for every read, which is premature at
this scale — but services importing each other's models would break the
ADR-0002 isolation rule.

## Decision

- One Postgres database shared by all services in the MVP.
- SQLAlchemy models and async session helpers live in a shared library,
  `libs/db` (`rag_db`) — services depend on `libs/*`, never on each other.
- The **ingestion service owns the single Alembic migration lineage**
  (`services/ingestion/alembic/`). One lineage avoids cross-service
  migration ordering problems; ingestion is the natural owner because it
  creates the root `documents` table.
- Model types stay portable (`sa.Uuid`, timezone-aware `DateTime`) so unit
  tests run on SQLite (aiosqlite) while CI integration tests run the real
  migrations on Postgres.

## Consequences

- Schema changes are reviewed in one place; services pick them up by
  bumping `rag-db`.
- A future split into per-service databases (if scale demands it) starts by
  moving tables out of `rag_db` behind service APIs.
