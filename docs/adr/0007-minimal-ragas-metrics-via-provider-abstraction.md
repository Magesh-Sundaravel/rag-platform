# ADR-0007: Minimal RAGAS-style metrics via the existing provider abstraction

- **Status:** Accepted
- **Date:** 2026-07-12

## Context

Phase 8 needs to score answer quality (faithfulness, answer relevancy,
context precision/recall — the standard RAGAS metric set) without
introducing a second LLM-integration path alongside `rag_providers`
(ADR-0006). The `ragas` PyPI package bundles its own LLM/embedding wrapper
layer (LangChain-based, OpenAI-first) and a heavier dependency footprint
than the platform otherwise carries; adopting it would mean maintaining two
parallel ways to call a hosted model provider.

## Decision

1. Implement a small `rag_evaluation` lib with judge-prompted scoring
   functions for the four core RAGAS metrics, using `GenerationProvider`
   (already defined in `rag_providers`) as the judge — no new provider
   protocol, no new dependency.
2. Each metric prompts the judge for a single `0.0`–`1.0` score with a
   strict output format, then parses and clamps it; unit tests use a
   `StubJudge` test double (module-local, mirrors how `bedrock.py` tests use
   `MagicMock`) so metric-parsing logic is deterministic and offline.
3. A minimal end-to-end run — a 3-example golden dataset scored by the real
   Bedrock judge — is an `llm_smoke`-marked test, per the existing
   secret-gated `llm-smoke` workflow (ADR-0006 §4).

## Consequences

- No new runtime dependency; the eval judge is swappable the same way
  embeddings/generation are (fake vs. Bedrock).
- Metric definitions are simplified relative to upstream RAGAS (single
  judge call per metric rather than multi-step statement decomposition);
  documented as a known limitation in `specs/phase-8-evaluation/spec.md`.
- If richer RAGAS fidelity is needed later, the upstream package can still
  be adopted independently without touching `rag_providers`.
