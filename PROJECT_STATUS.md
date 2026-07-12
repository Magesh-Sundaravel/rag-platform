# Project Status

- **Current Phase:** 7 — Generation (starting)
- **Completed:** Phases 0-6 (foundation; ingestion; worker; chunking; metadata filters; embeddings + pgvector HNSW; hybrid retrieval)
- **Next:** Phase 7 generation service (Gemini answer synthesis, citations, memory)
- **Blocked:** none (real Gemini exercised via llm-smoke workflow)
- **Tests:** 112 passed + 1 gated (CI/LLM-only), coverage 95%
- **Last Commit:** feat(retrieval): hybrid search (vector KNN + Postgres FTS + RRF)
