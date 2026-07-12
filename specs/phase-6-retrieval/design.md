# Phase 6 Design

## `libs/contracts/src/rag_contracts/search.py`

- `SearchRequest`: `query: str`, `top_k: int = 10` (1-100), `filters: list[MetadataFilter] = []`.
- `SearchResultItem`: `chunk_id`, `document_id`, `text`, `score: float`, `metadata: dict`.
- `SearchResponse`: `items: list[SearchResultItem]`, `query: str`.

## `services/retrieval/src/retrieval`

- `db.py` — engine/session-factory wiring, same shape as
  `ingestion/db.py` (each service owns its own `get_session`; no
  cross-service imports per ADR-0002).
- `config.py` — adds `database_url` and `embedding_provider` (same fields
  as processing's `Settings`).
- `vector_search.py` — `vector_knn(session, query_vector, k, predicates)`:
  `select(Chunk).where(*predicates).order_by(Chunk.embedding.cosine_distance(query_vector)).limit(k)`,
  returns `[(Chunk, distance)]`.
- `fulltext_search.py` — `fulltext_search(session, query, k, predicates)`:
  raw `to_tsvector`/`plainto_tsquery`/`ts_rank` via `sqlalchemy.func`,
  filtered by the WHERE-matches predicate, ordered by rank desc, returns
  `[(Chunk, rank)]`.
- `hybrid.py` — `reciprocal_rank_fusion(rankings: list[list[UUID]], k: int = 60) -> dict[UUID, float]`:
  standard RRF, `score[id] += 1 / (k + rank)` for each list the id appears
  in (1-indexed rank). Pure function, no I/O.
- `search.py` — `hybrid_search(session, embedder, request) -> list[SearchResultItem]`:
  builds predicates from `request.filters`, embeds `request.query`, runs
  vector KNN and full-text search concurrently (`asyncio.gather`), fuses
  with `reciprocal_rank_fusion`, hydrates the top `top_k` chunks (dedup by
  chunk id, keep the highest-scoring occurrence) into
  `SearchResultItem`s.
- `routes.py` — `POST /search` -> `SearchResponse`.

## Schema

Migration 0005: `CREATE INDEX ix_chunks_text_fts ON chunks USING gin
(to_tsvector('english', text))`. No new column — the functional index
covers query-time `to_tsvector` calls (Postgres matches the expression).

## Why RRF over score-blending

Vector cosine distance and `ts_rank` are on unrelated scales impossible to
weight meaningfully without tuning data. RRF only needs each list's rank
order, is parameter-light (`k=60` is the standard default), and is the
common baseline for hybrid search — appropriate for an MVP with no
eval harness yet (that's Phase 8).
