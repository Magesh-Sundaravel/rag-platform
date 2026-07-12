# Phase 1 Tasks

1. Create `libs/db` workspace member (models + session). → verify: mypy, unit tests import.
2. Contracts: document models. → verify: unit test round-trip.
3. Parsing module w/ tests (txt, md, pdf, unsupported, bad utf-8).
4. Repository: create w/ dedup + versioning + job outbox row; get/list/delete. → verify: SQLite unit tests.
5. Routes + app wiring. → verify: API tests via httpx ASGI.
6. Alembic setup + migration 0001. → verify: CI integration test runs `upgrade head`.
7. Integration tests (skipif no `RAG_TEST_DB_URL`); CI: postgres service container.
8. ADR-0004; docs + README + PROJECT_STATUS updates.
9. Gates green → commit → push → CI green.
