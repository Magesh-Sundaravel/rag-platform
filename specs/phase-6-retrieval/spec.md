# Phase 6 Specification: Hybrid Retrieval

- **Status:** Accepted
- **Date:** 2026-07-12
- **Phase:** 6 of 10

## Problem

Chunks now have embeddings (Phase 5) and metadata filters (Phase 4), but
there is no query path. Vector-only search misses exact keyword/acronym
matches; keyword-only search misses paraphrase/semantic matches. The
retrieval service needs a single query API that combines both.

## Scope

1. `POST /search` on the retrieval service: `{query, top_k, filters}` ->
   ranked chunks.
2. Vector KNN: embed the query (same `EmbeddingProvider` abstraction as
   Phase 5), pgvector cosine-distance (`<=>`, HNSW index from migration
   0004).
3. Full-text search: Postgres `to_tsvector('english', text)` vs
   `plainto_tsquery('english', query)`, ranked by `ts_rank`. New migration
   0005 adds a GIN index on the functional tsvector expression.
4. Fusion: Reciprocal Rank Fusion (RRF, `k=60`) combines the two ranked
   lists into one score per chunk; a pure, DB-free function.
5. Metadata filters (Phase 4 `metadata_predicates`) applied to both
   underlying queries before fusion.

## Out of scope (later phases)

- Cross-encoder reranking (roadmap mentions it under retrieval, but
  PROJECT_STATUS scopes Phase 6 to vector + FTS + RRF only; rerank is
  deferred).
- Generation / answer synthesis (Phase 7).

## Determinism / portability contract

- RRF fusion is pure and unit-tested without a database.
- Vector KNN and full-text search use Postgres-only SQL (`<=>` operator,
  `to_tsvector`); they are exercised by the existing Postgres integration
  test lane (`RAG_TEST_DB_URL`, mirrors Phases 1/2), not SQLite unit tests.

## Acceptance Criteria

- [ ] `POST /search` returns fused, filtered results ordered by RRF score.
- [ ] RRF fusion unit-tested: item order, tie-handling, empty-list inputs.
- [ ] Migration 0005 applies on CI Postgres (GIN index on tsvector expr).
- [ ] Vector KNN and full-text search covered by Postgres integration tests.
- [ ] Gates green.
