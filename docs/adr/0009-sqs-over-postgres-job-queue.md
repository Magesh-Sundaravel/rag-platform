# ADR-0009: AWS SQS instead of the Postgres job queue

- **Status:** Accepted
- **Date:** 2026-11-09
- **Supersedes:** ADR-0005

## Context

ADR-0005 used a Postgres `jobs` table as the queue between ingestion and
processing. Its known gaps: a worker that crashes mid-job leaves the job
stuck `in_progress` forever, workers poll the database constantly, and
queue traffic shares the database with real data. The platform now deploys
to AWS (ECS/Fargate), so a managed queue is available.

## Decision

1. Replace the `jobs` table with an SQS queue plus a dead-letter queue (DLQ).
   The `Job` model is removed and a migration drops the table.
2. Ingestion commits the document, then sends a `process_document` message.
   If the send fails, ingestion deletes the document it just saved and
   returns 503, so the client retries. No outbox, no background sweeper.
3. Processing long-polls SQS and deletes each message only after it
   succeeds. If a worker crashes, the visibility timeout makes the message
   reappear for another worker.
4. Retries and dead-lettering use the SQS redrive policy
   (`maxReceiveCount = 3` → DLQ). On the last failed attempt, the document
   is marked `failed`.

## Consequences

- Stuck jobs and database polling are gone; workers scale on queue depth.
- Local dev and docker-compose run ElasticMQ (SQS-compatible) instead of
  real SQS.
- Delivery is at-least-once: a message can be processed twice (e.g. a send
  that timed out but actually succeeded, or a visibility-timeout expiry).
  Processing is idempotent (it replaces a document's chunks), and a message
  for a missing document is acknowledged and dropped.
- A crash between commit and send leaves a document `pending` with no
  message. Re-uploading the same content re-sends the message (a pending
  duplicate is not rejected with 409), which also recovers documents left
  `pending` by the cutover from the `jobs` table.
- `RAG_MAX_RECEIVE_COUNT` in processing must match the queue's
  `maxReceiveCount` in Terraform, or documents are marked `failed` at the
  wrong attempt.
- The SQS visibility timeout must exceed the slowest document's processing
  time, or the message is redelivered while still being processed.
