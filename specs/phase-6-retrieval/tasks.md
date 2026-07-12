# Phase 6 Tasks

1. `rag_contracts.search` request/response models. → verify: unit tests.
2. Migration 0005: GIN index on `to_tsvector('english', text)`. → verify: CI alembic upgrade.
3. `retrieval` service: `db.py`, `config.py` (database_url, embedding_provider). → verify: import + settings test.
4. `vector_search.py`, `fulltext_search.py`. → verify: Postgres integration tests.
5. `hybrid.py` RRF fusion. → verify: unit tests (order, ties, empty inputs).
6. `search.py` orchestration + `POST /search` route. → verify: Postgres integration test through the HTTP API.
7. Docs/status; gates; commit; push; PR; merge.
