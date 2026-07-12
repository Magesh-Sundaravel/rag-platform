# Phase 9 Tasks

1. `rag_guardrails` lib: prompt-injection detection + PII redaction. → verify: unit tests (known phrases/patterns, benign text untouched).
2. Wire guardrails into generation `/query` route. → verify: API tests (flagged question -> 422 before retrieval call; PII in answer redacted in response).
3. `rag_common.tracing`: `configure_tracing()` + OTel deps. → verify: unit tests (no-op without endpoint, real provider + httpx instrumentation with one).
4. Wire tracing into `app_factory` (`configure_tracing` + `FastAPIInstrumentor`). → verify: existing health-endpoint tests still pass for all 4 services.
5. Docs/status; ADR-0008; gates; commit.
