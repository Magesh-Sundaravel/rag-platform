# Project Status

- **Current Phase:** 2 — Processing pipeline (starting)
- **Completed:** Phase 0 foundation; Phase 1 ingestion (documents+jobs schema, alembic, upload/dedup/versioning API, job outbox)
- **Next:** Phase 2 worker loop (Postgres job queue), normalization, metadata extraction
- **Blocked:** real Gemini calls locally (key only in CI secret; provider fakes per ADR-0003)
- **Tests:** 45 passed + 1 integration (CI-only), coverage 97%
- **Last Commit:** feat(ingestion): document upload, dedup, versioning (phase 1)
