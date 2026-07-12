# Phase 9 Design

## `rag_guardrails` lib

- `prompt_injection.py`:
  - `_INJECTION_PATTERNS`: compiled case-insensitive regexes for phrases
    like `ignore (all )?(the )?(previous|above) instructions`, `reveal
    (your )?(system )?prompt`, `disregard (the )?(above|prior)`, `you are
    now`, `act as (if )?you (have no|are not) restrictions`.
  - `detect_prompt_injection(text: str) -> bool`: `True` if any pattern
    matches.
- `pii.py`:
  - `_PII_PATTERNS: dict[str, re.Pattern[str]]` — `email`, `phone`,
    `credit_card`, `ssn`.
  - `redact_pii(text: str) -> str`: replaces each pattern's matches with
    `[REDACTED_<KIND>]` (kind uppercased), applied in a fixed order so
    overlapping patterns don't double-redact.

Both modules are dependency-free (`re` only); no provider, no fakes needed
for tests.

## Generation service wiring

- `routes.py`: at the top of `query()`, call
  `detect_prompt_injection(request.question)`; if `True`, raise
  `InvalidInputError("question was flagged as a potential prompt injection")`
  (existing `rag_common.exceptions`, renders as `422`) before the retrieval
  call.
- After `generator.generate(prompt)`, redact `result.text` with
  `redact_pii()` before it's used for citation extraction and the response
  (citations' snippets are left as-is; they're sourced from ingested
  documents, not raw LLM output — noted as an out-of-scope simplification).

## `rag_common.tracing`

```python
def configure_tracing(settings: BaseServiceSettings) -> None:
    if not settings.otel_exporter_endpoint:
        return  # OTel's default no-op TracerProvider stays in place
    resource = Resource.create({"service.name": settings.service_name})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_endpoint)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    HTTPXClientInstrumentor().instrument()
```

- `app_factory.create_app()`: calls `configure_tracing(settings)` right
  after `configure_logging`, then, after building `app`,
  `FastAPIInstrumentor.instrument_app(app)` unconditionally (cheap ASGI
  middleware; produces spans regardless of exporter, matching typical OTel
  usage where instrumentation and export are separate concerns).
- `BaseServiceSettings.otel_exporter_endpoint: str | None = None`
  (`RAG_OTEL_EXPORTER_ENDPOINT`).

## Dependencies

`rag_common` gains `opentelemetry-sdk`,
`opentelemetry-instrumentation-fastapi`,
`opentelemetry-instrumentation-httpx`,
`opentelemetry-exporter-otlp-proto-http`. `rag_guardrails` gains none
(stdlib `re` only) beyond `rag_common` (for `InvalidInputError`, imported
directly by the generation service, not by the lib itself — the lib stays
framework-agnostic and returns plain booleans/strings).
