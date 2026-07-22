# Project Status

- **Current Phase:** 10 — AWS deployment (starting)
- **Completed:** Phases 0-9 (foundation; ingestion; worker; chunking; metadata filters; embeddings + pgvector HNSW; hybrid retrieval; generation with citations; RAGAS evaluation; guardrails + OpenTelemetry)
- **Next:** Phase 10 AWS deployment (Terraform, ECS Fargate, RDS PostgreSQL)
- **Blocked:** none (real Bedrock exercised via llm-smoke workflow)
- **Tests:** 169 passed + 11 gated (CI/LLM-only + Postgres-only), coverage 94%
- **Last Commit:** feat(guardrails): heuristic guardrails + OpenTelemetry tracing (phase 9)
