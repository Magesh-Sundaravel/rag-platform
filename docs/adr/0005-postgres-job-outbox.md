# ADR-0005: Postgres job outbox instead of a message broker

- **Status:** Accepted
- **Date:** 2026-07-12

## Context

Ingestion must hand documents to the async processing pipeline (Phase 2)
without losing work: a document that is saved but never processed, or a
processing message for a document that was rolled back, are both bugs.
A dedicated broker (Redis Streams, Pub/Sub, RabbitMQ) adds an infrastructure
component and — without an outbox — a dual-write consistency problem.

## Decision

Use a `jobs` table in the shared Postgres database as a transactional
outbox/queue. Every successful ingest inserts the document row **and** a
`pending` job row in the same transaction. Phase 2 workers poll with
`SELECT ... FOR UPDATE SKIP LOCKED`, tracking `attempts`/`max_attempts` for
retries.

## Consequences

- Exactly-once handoff between ingest and processing with zero extra
  infrastructure; at MVP volumes polling Postgres is more than sufficient.
- If throughput ever outgrows this, the same outbox table can feed a real
  broker without changing the ingestion write path.
