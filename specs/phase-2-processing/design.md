# Phase 2 Design

## Modules (services/processing)

- `processing/normalize.py` — `normalize_text(str) -> str` (NFKC, CRLF→LF,
  strip control chars except `\n\t`, collapse 3+ newlines to 2, collapse
  spaces/tabs).
- `processing/metadata.py` — `extract_metadata(filename, text) -> DocMetadata`
  (contracts model): `title`, `language` (`en`/`unknown` via English
  stopword ratio ≥ 0.15 of first 200 words), `char_count`, `token_count`
  (~4 chars/token estimate; swap for a real tokenizer later if needed).
- `processing/pipeline.py` — `process_document(session, document) -> None`:
  normalize raw text, extract metadata, update document status
  (`processed`). Chunking/embedding hooks added in Phases 3/5.
- `processing/worker.py` — job queue mechanics:
  - `claim_job(session)` — `select(Job).where(status=="pending")
    .with_for_update(skip_locked=True).limit(1)`; sets `in_progress`.
  - `run_job(session, job)` — dispatch by `job_type`, success → `done`;
    failure → attempts+1; attempts >= max_attempts → `dead` + document
    `failed`, else back to `pending`.
  - `worker_loop(factory, poll_interval, run_once=False)` — async loop;
    `run_once` for tests; app startup launches it as a background task
    (env `RAG_WORKER_ENABLED`, default true; disabled in tests).

## Config additions

`processing.config.Settings`: `database_url`, `poll_interval_seconds`
(default 1.0), `worker_enabled` (default True).

## Contracts

`rag_contracts.processing.DocMetadata` — shared later with chunk metadata.

## Failure semantics

Each job attempt runs in its own transaction. The claim (status →
`in_progress`) commits immediately so other workers skip it; crash recovery
(stuck `in_progress`) is documented tech debt for the MVP.
