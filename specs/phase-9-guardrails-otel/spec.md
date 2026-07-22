# Phase 9 Specification: Guardrails + OpenTelemetry

- **Status:** Accepted
- **Date:** 2026-07-12
- **Phase:** 9 of 10

## Problem

The generation endpoint accepts free-text questions and returns LLM output
directly to the caller with no input/output safety checks. Separately, the
platform has four services calling each other over HTTP (generation ->
retrieval) with no way to correlate a request across service boundaries or
see per-service latency/error rates.

## Scope

### Guardrails (`rag_guardrails`, wired into `generation`)

1. `detect_prompt_injection(text) -> bool`: regex/phrase heuristics for
   common injection attempts ("ignore previous instructions", "reveal your
   system prompt", "disregard the above", etc., case-insensitive).
2. `redact_pii(text) -> str`: regex-based redaction of emails, phone
   numbers, credit-card-like digit runs, and SSN-like patterns, replacing
   matches with `[REDACTED_<KIND>]`.
3. `POST /query` wiring: reject a flagged question with `422
   invalid_input` before calling retrieval (no wasted retrieval/LLM call);
   redact PII from the answer text before it's returned.

### OpenTelemetry (`rag_common.tracing`, wired into `app_factory` + generation's retrieval client)

1. `configure_tracing(settings)`: no-ops when
   `settings.otel_exporter_endpoint` is unset (default); otherwise installs
   a `TracerProvider` (resource `service.name=<service>`) with an
   OTLP/HTTP exporter and instruments the process's `httpx` client calls.
2. `create_app()` always calls `FastAPIInstrumentor.instrument_app(app)` so
   every service produces request spans regardless of exporter
   configuration (harmless without one — spans are created and dropped).
3. Settings: `otel_exporter_endpoint: str | None = None`.

## Out of scope

- LLM-judged safety classification (ADR-0008 — heuristics only).
- Tracing database queries (SQLAlchemy instrumentation) or the async
  worker loop; scoped to HTTP request spans for this phase.
- A deployed collector (Phase 10, AWS deployment, will wire a real
  endpoint).

## Testing

- Guardrail functions: pure unit tests (known injection phrases flagged,
  benign questions pass; each PII pattern redacted, non-PII text
  untouched).
- Generation route: API tests asserting a flagged question gets `422`
  before any retrieval call, and a PII-bearing fake answer is redacted in
  the response.
- Tracing: unit test that `configure_tracing` is a no-op without an
  endpoint (global tracer provider unchanged) and installs a
  `TracerProvider` when one is set; no test depends on a live collector.

## Acceptance Criteria

- [x] Prompt-injection questions are rejected with `422` before retrieval
      is called.
- [x] PII patterns in generated answers are redacted before the response
      is returned.
- [x] `configure_tracing` is inert by default; installs a real provider +
      httpx instrumentation only when `RAG_OTEL_EXPORTER_ENDPOINT` is set.
- [x] Every service's FastAPI app is instrumented (spans exist locally at
      zero config).
- [x] Gates green.
