# ADR-0005: Postgres job queue instead of a message broker

- **Status:** Accepted
- **Date:** 2026-07-12

## Context

Ingestion hands work to processing asynchronously. Options: a broker
(RabbitMQ/Redis Streams/Pub-Sub) or a Postgres-backed queue. We already run
Postgres, volumes are modest (MVP), and the outbox row is written in the same
transaction as the document — giving exactly-once handoff without dual-write
problems.

## Decision

Use the `jobs` table as the queue:

- Producers insert `pending` rows transactionally with their domain writes
  (outbox pattern).
- Workers claim with `SELECT ... FOR UPDATE SKIP LOCKED LIMIT 1`, flip to
  `in_progress`, and commit the claim; multiple workers scale horizontally
  without double-processing.
- Failures increment `attempts`; at `max_attempts` the job becomes `dead`
  (dead-letter stays in the table) and the document is marked `failed`.

## Consequences

- No new infrastructure; transactional enqueue for free.
- Polling latency (~1s default) instead of push; acceptable for document
  processing.
- Known MVP gap: a worker crash mid-job leaves `in_progress` rows; a
  timeout-based reaper is documented tech debt.
- If throughput outgrows Postgres, swap the worker's claim/complete functions
  for a broker consumer — producers keep the outbox and a relay ships rows.
