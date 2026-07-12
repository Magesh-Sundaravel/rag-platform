# Phase 5 Specification: Embeddings + pgvector

- **Status:** Accepted
- **Date:** 2026-07-12
- **Phase:** 5 of 10

## Problem

Chunks need vector representations for semantic retrieval. LLM/API access is
CI-only (secret `GEMINI_API_KEY`), so all local/unit paths must run against a
deterministic fake (ADR-0003/ADR-0006).

## Scope

1. New workspace lib `libs/providers` (`rag_providers`):
   - `EmbeddingProvider` protocol: `dimension: int`,
     `async embed(texts) -> list[list[float]]`.
   - `FakeEmbeddingProvider`: sha256(text)-seeded RNG → 768-dim unit vector;
     deterministic across processes, cheap, dependency-free.
   - `GeminiEmbeddingProvider`: `gemini-embedding-001` via `google-genai`
     (`GEMINI_API_KEY` env), `output_dimensionality=768`, batched.
2. `chunks.embedding vector(768)` (pgvector) + HNSW index
   (`vector_cosine_ops`) — migration 0004 with `CREATE EXTENSION IF NOT
   EXISTS vector`.
3. Processing worker embeds chunk texts right after chunking (provider
   selected by `RAG_EMBEDDING_PROVIDER`, default `fake`).
4. `.github/workflows/llm-smoke.yml` (workflow_dispatch + push to main,
   gated on secret presence) runs real-provider smoke tests
   (`tests marked llm_smoke`): embed a string (Phase 5), generate an answer
   (Phase 7), minimal RAGAS run (Phase 8).

## Determinism contract (unit-tested)

- Same text → same vector; different text → different vector.
- Unit norm (|v| ≈ 1); dimension 768.

## Acceptance Criteria

- [ ] Fake provider deterministic + normalized; worker persists embeddings.
- [ ] Migration 0004 applies on CI Postgres (extension + column + HNSW).
- [ ] Gemini provider unit-tested against a mocked client; real call covered
  by llm-smoke workflow.
- [ ] Gates green.
