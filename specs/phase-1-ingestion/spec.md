# Phase 1 Specification: Document Ingestion

- **Status:** Accepted
- **Date:** 2026-07-12
- **Phase:** 1 of 10

## Problem

The platform needs a durable entry point for documents: upload, parse to raw
text, deduplicate, version, and hand off to async processing.

## Goals

1. `documents` table (SQLAlchemy 2.0 async + asyncpg) with alembic migrations
   owned by the ingestion service (single migration lineage, see ADR-0004).
2. `POST /documents` multipart upload for `.txt`, `.md` (UTF-8 text) and
   `.pdf` (text extraction via pypdf).
3. Dedup: sha256 of raw bytes; exact duplicate → `409 Conflict`.
4. Versioning: re-upload of a *changed* file with the same filename creates a
   new row with `version = max(version) + 1`.
5. `GET /documents/{id}`, `GET /documents` (offset/limit pagination),
   `DELETE /documents/{id}`.
6. Every successful ingest writes a `pending` job row (outbox for Phase 2)
   in the same transaction.

## Schema

`documents`: `id uuid pk`, `filename text`, `content_type text`,
`content_hash char(64) unique`, `version int`, `status text`
(`pending|processed|failed`), `raw_text text`, `created_at timestamptz`.

`jobs` (created now, consumed in Phase 2): `id uuid pk`,
`document_id uuid fk cascade`, `job_type text`, `status text`,
`attempts int`, `max_attempts int`, `last_error text`,
`created_at/updated_at timestamptz`.

## Non-Goals

- Chunking, embedding (Phases 3/5). Worker loop (Phase 2).
- Object storage for original binaries — raw extracted text only (MVP).

## Testing

- Unit/API tests run against SQLite (aiosqlite) via dependency override —
  no local Postgres required.
- Integration tests against real Postgres run only when `RAG_TEST_DB_URL`
  is set (CI service container `pgvector/pgvector:pg16`); locally they skip.
- Coverage gate stays ≥ 90%.

## Acceptance Criteria

- [ ] Upload txt/md/pdf returns 201 with document payload (contracts model).
- [ ] Exact duplicate upload returns 409.
- [ ] Changed content, same filename → version increments.
- [ ] List pagination + get + delete behave per REST conventions.
- [ ] Pending job row written atomically with the document.
- [ ] Alembic `upgrade head` creates the schema on Postgres (verified in CI).
- [ ] All quality gates green.
