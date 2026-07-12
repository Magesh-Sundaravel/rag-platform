# Project Status

- **Current Phase:** 1 — Document ingestion (complete, pending review/merge)
- **Completed:** Phase 0 foundation; Phase 1: `libs/db` (shared models + async sessions), document contracts, txt/md/pdf parsing, upload API with sha256 dedup + filename versioning, jobs outbox (ADR-0005), Alembic migration 0001, SQLite unit/API tests + Postgres integration tests in CI
- **Next:** Phase 2 processing pipeline (job workers consume the outbox)
- **Blocked:** real Gemini calls (no API key — building against provider fakes per ADR-0003)
- **Tests:** 49 passed, 1 skipped locally (Postgres integration runs in CI), coverage ~97%
- **Last Commit:** see branch `worktree-phase-1-ingestion`
