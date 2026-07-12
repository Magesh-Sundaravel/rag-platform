# Project Status

- **Current Phase:** 5 — Embeddings (starting)
- **Completed:** Phases 0-4 (foundation; ingestion; processing worker; chunking; metadata filters + GIN index)
- **Next:** Phase 5 EmbeddingProvider protocol, fake + Gemini providers, pgvector column + HNSW
- **Blocked:** real Gemini calls locally (key only in CI secret; provider fakes per ADR-0003)
- **Tests:** 87 passed + 3 integration (CI-only), coverage 96%
- **Last Commit:** feat(retrieval): metadata filter contracts and JSONB predicates (phase 4)
