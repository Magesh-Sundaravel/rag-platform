# Phase 2 Specification: Processing Pipeline

- **Status:** Accepted
- **Date:** 2026-07-12
- **Phase:** 2 of 10

## Problem

Ingested documents sit in `pending` with a job row (Phase 1 outbox). The
processing service must consume those jobs asynchronously, reliably, and
idempotently: normalize text, extract metadata, and (Phases 3/5) chunk and
embed.

## Decisions

- **Postgres as the job queue** (ADR-0005): `SELECT ... FOR UPDATE SKIP
  LOCKED` claims one job per worker iteration; no broker (Redis/RabbitMQ)
  in the MVP.
- Retry with `attempts`/`max_attempts`; when exhausted, job status becomes
  `dead` (dead-letter kept in the table for inspection) and the document is
  marked `failed`.

## Scope

1. Worker loop in the processing service: async poll loop with configurable
   interval, claims `pending` jobs (`FOR UPDATE SKIP LOCKED`), runs the
   pipeline, marks `done`/`pending`(retry)/`dead`.
2. Normalization: unicode NFKC, newline normalization, collapse repeated
   whitespace, strip control chars.
3. Metadata extraction: title heuristic (first markdown heading or first
   non-empty line), language detection (stopword-ratio heuristic, en/other),
   char count, estimated token count (`len // 4` approximation, documented).
4. Pipeline result persisted on the document (status → `processed`) with
   extracted metadata stored on chunk rows from Phase 3 onward; for now the
   job completes and status transitions are observable.

## Job state machine

`pending → in_progress → done | pending(retry, attempts+1) | dead`

## Non-Goals

- Chunking (Phase 3), embedding (Phase 5).
- Horizontal scaling test of multiple workers (design supports it via SKIP
  LOCKED; verified with a unit test of claim semantics on Postgres in CI).

## Testing

- Pure functions (normalize, metadata) — direct unit tests.
- Worker loop — unit tests on SQLite (FOR UPDATE is a no-op there) covering
  success, retry, dead-letter; claim-contention test runs on Postgres in CI.

## Acceptance Criteria

- [ ] Worker processes a pending job end-to-end; document → `processed`.
- [ ] Failing pipeline retries up to `max_attempts`, then `dead` + document `failed`.
- [ ] Normalization and metadata functions behave per unit tests.
- [ ] ADR-0004/0005 recorded; gates green.
