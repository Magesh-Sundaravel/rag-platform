# Project Status

- **Current Phase:** 3 — Chunking (starting)
- **Completed:** Phases 0-2 (foundation; ingestion API; job-queue worker with retry/dead-letter, normalization, metadata extraction)
- **Next:** Phase 3 chunkers (fixed-size + recursive) and chunks table
- **Blocked:** real Gemini calls locally (key only in CI secret; provider fakes per ADR-0003)
- **Tests:** 65 passed + 3 integration (CI-only), coverage 95%
- **Last Commit:** feat(processing): job-queue worker, normalization, metadata (phase 2)
