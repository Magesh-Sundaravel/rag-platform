# Phase 1 Design

## New library: `libs/db` (`rag_db`)

All services share one Postgres instance in the MVP (ADR-0004). To keep the
"services never import each other" rule intact, SQLAlchemy models and session
helpers live in a shared library:

- `rag_db.models` — `Base`, `Document`, `Job` (later `Chunk`).
  - Portable types: `sa.Uuid`, `JSONB().with_variant(JSON, "sqlite")` so unit
    tests can run on SQLite.
- `rag_db.session` — `create_session_factory(url)` returning
  `async_sessionmaker[AsyncSession]`.

## Ingestion service

- `ingestion/config.py` — adds `database_url` (env `RAG_DATABASE_URL`).
- `ingestion/db.py` — lazy engine/session-factory wiring + `get_session`
  FastAPI dependency (override point for tests).
- `ingestion/parsing.py` — `extract_text(filename, content_type, data)`;
  txt/md decode UTF-8 (reject undecodable), pdf via `pypdf.PdfReader`.
  Unsupported type → `InvalidInputError` (422).
- `ingestion/routes.py` — APIRouter with the four endpoints; dedup + version
  logic in `ingestion/repository.py` for testability.
- Job row: `job_type="process_document"`, `status="pending"`,
  `max_attempts=3`, same transaction as document insert.

## Migrations

`services/ingestion/alembic/` with async env.py (`run_sync`), single lineage
`0001_documents_jobs`. Excluded from coverage (not under `src/`).

## API (contracts)

`rag_contracts.documents`: `DocumentStatus` (str enum), `DocumentOut`,
`DocumentListOut` (items + total + offset + limit).

## Error mapping

- duplicate hash → `ConflictError` (409)
- unknown id → `NotFoundError` (404)
- unsupported/undecodable file → `InvalidInputError` (422)
