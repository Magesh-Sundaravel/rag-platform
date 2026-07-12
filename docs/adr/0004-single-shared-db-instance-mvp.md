# ADR-0004: Single shared Postgres instance per MVP

- **Status:** Accepted
- **Date:** 2026-07-12

## Context

ADR-0002 mandates that each service owns its tables and that other services
go through the owning service's API. Running four Postgres instances (or four
schemas with duplicated migration tooling) for an MVP adds operational cost
with no learning value, and the processing worker / retrieval service need
efficient direct access to documents and chunks.

## Decision

1. One Postgres instance (with pgvector) serves all services in the MVP.
2. ORM models live in the shared library `libs/db` (`rag_db`) so services
   still never import each other.
3. The ingestion service owns the single alembic migration lineage
   (`services/ingestion/alembic/`), because it owns the root `documents`
   table; later tables (jobs consumption, chunks, embeddings, FTS) extend the
   same lineage.
4. Logical ownership is still documented per table: `documents` → ingestion,
   `jobs`/`chunks` writes → processing, `chunks` reads → retrieval.

## Consequences

- Cheaper local dev and CI (one `pgvector/pgvector:pg16` container).
- Table-level coupling is accepted and contained in `rag_db`; splitting into
  per-service databases later means moving models out of `rag_db` and
  introducing service APIs/replication for cross-service reads.
