# ADR-0008: Heuristic guardrails; OpenTelemetry gated by exporter config

- **Status:** Accepted
- **Date:** 2026-07-12

## Context

Phase 9 needs (a) basic safety guardrails around the LLM-facing generation
endpoint and (b) distributed tracing across the four services. Both must
stay offline-first per the project's existing conventions (ADR-0006):
local dev and the main CI test job never require network access, external
collectors, or secrets.

## Decision

1. **Guardrails** (`rag_guardrails`) are pure heuristics — regex-based
   prompt-injection phrase detection and PII redaction (email, phone,
   credit-card, SSN patterns) — not an LLM-judged safety classifier. No
   provider call, no network, trivially deterministic and unit-testable.
   Wired into the generation service only: reject flagged questions
   (`422`) before calling retrieval, redact PII from the answer before
   returning it.
2. **OpenTelemetry** is added to `rag_common` and always instruments each
   FastAPI app (`FastAPIInstrumentor`) so per-service request spans exist
   locally at zero configuration cost. The actual exporter is **gated on
   `RAG_OTEL_EXPORTER_ENDPOINT`**: unset (the local/CI default) leaves
   OpenTelemetry's built-in no-op `TracerProvider` in place — spans are
   created and dropped, no thread, no network, no test noise. Setting the
   endpoint installs a real `TracerProvider` with an OTLP/HTTP exporter
   and also enables `HTTPXClientInstrumentor` so the generation ->
   retrieval HTTP call carries `traceparent` and the two services' spans
   join into one trace.

## Consequences

- Guardrail checks add no latency-sensitive dependency and are exhaustively
  unit-tested without fakes or mocks.
- Tracing is genuinely opt-in: `docker compose` local dev and `pytest` never
  spin up exporters or background threads; pointing
  `RAG_OTEL_EXPORTER_ENDPOINT` at a collector (e.g. in AWS later, Phase 10)
  is a config-only change, no code change.
- Regex-based guardrails are a known-limited approach (won't catch novel
  phrasing); documented as a limitation in `specs/phase-9-guardrails-otel/spec.md`.
