# Phase 2 Tasks

1. ADR-0005 postgres job queue. → verify: doc review.
2. Contracts `DocMetadata`. → verify: unit test.
3. `normalize.py` + tests (unicode, whitespace, control chars).
4. `metadata.py` + tests (title md/plain, language, counts).
5. `pipeline.py` + `worker.py` + tests (done/retry/dead paths, run_once loop).
6. App wiring: lifespan background worker, config flags. → verify: health test still green, worker disabled in tests.
7. Postgres claim-contention integration test (CI).
8. Docs + status updates; gates; commit; push; CI green.
