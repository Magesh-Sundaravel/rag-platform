# Phase 5 Tasks

1. ADR-0006 provider abstraction + Bedrock SDK choice.
2. `rag_providers` lib: protocol, fake, factory. → verify: determinism/norm unit tests.
3. Bedrock embedding provider. → verify: mocked-client unit test; llm-smoke real test.
4. `Chunk.embedding` + migration 0004. → verify: CI alembic upgrade.
5. Pipeline/worker embedding integration. → verify: worker test asserts vectors persisted.
6. llm-smoke workflow + smoke test (embed). → verify: `gh workflow run` after push.
7. Docs/status; gates; commit; push; CI green.
