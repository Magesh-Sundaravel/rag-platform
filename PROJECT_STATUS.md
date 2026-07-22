# Project Status

- **Current Phase:** 10 — AWS deployment (Terraform/CI/docs scaffolded)
- **Completed:** Phases 0-9 (foundation; ingestion; worker; chunking; metadata filters; embeddings + pgvector HNSW; hybrid retrieval; generation with citations; RAGAS evaluation; guardrails + OpenTelemetry)
- **Next:** Validate/apply the AWS stack in a real account and execute the first deployed smoke test
- **Blocked:** none (real Bedrock exercised via llm-smoke workflow)
- **Tests:** 169 passed + 11 gated (CI/LLM-only + Postgres-only), coverage 94%
- **Last Commit:** feat(guardrails): heuristic guardrails + OpenTelemetry tracing (phase 9)
