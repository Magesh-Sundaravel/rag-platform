# ADR-0006: Provider abstraction with deterministic fakes; Gemini via google-genai

- **Status:** Accepted
- **Date:** 2026-07-12

## Context

The platform needs embeddings (Phase 5) and generation (Phase 7). The Gemini
API key exists **only** as a GitHub Actions secret; local development and the
main CI test job must never require network or secrets. Tests must be
deterministic.

## Decision

1. Provider protocols (`EmbeddingProvider`, `GenerationProvider`) live in a
   dedicated workspace lib `libs/providers` (`rag_providers`), importable by
   any service, keeping the `google-genai` dependency out of `rag_common`.
2. Every protocol ships a **deterministic fake** used by all local/unit
   tests: embeddings are sha256-seeded unit vectors; generation echoes
   context ids so citation logic is testable.
3. Real providers use the `google-genai` SDK (`GEMINI_API_KEY` env):
   `gemini-embedding-001` (768 dims) and `gemini-2.5-flash`.
4. Real-provider tests run only in the `llm-smoke` workflow (secret-gated,
   `workflow_dispatch` + push to main); they self-skip when the key is
   absent.

## Consequences

- Local dev is offline-first and fast; provider swap is a config change
  (`RAG_EMBEDDING_PROVIDER` / `RAG_GENERATION_PROVIDER`).
- Fake vectors have no semantic meaning — ranking-quality assertions belong
  to the (LLM-gated) evaluation phase, not unit tests.
- Vendor migration (e.g. Vertex AI) touches one lib.
