# Phase 3 Specification: Chunking

- **Status:** Accepted
- **Date:** 2026-07-12
- **Phase:** 3 of 10

## Problem

Processed documents must be split into retrieval-sized chunks with overlap,
persisted with per-chunk metadata, under a strategy that is configurable and
swappable.

## Scope

1. `Chunker` protocol: `chunk(text) -> list[str]` — own implementation, **no
   LangChain dependency**.
2. `FixedSizeChunker(chunk_size, overlap)` — character windows with overlap.
3. `RecursiveCharacterChunker(chunk_size, overlap)` — splits on a separator
   hierarchy (`\n\n`, `\n`, sentence end, space, hard cut), merging pieces up
   to `chunk_size` with overlap carried between chunks.
4. `chunks` table: `id`, `document_id` FK (cascade), `chunk_index`, `text`,
   `token_count`, `metadata` JSONB; unique `(document_id, chunk_index)`.
5. Config-driven strategy selection in the processing service
   (`RAG_CHUNK_STRATEGY` = `fixed` | `recursive`, `RAG_CHUNK_SIZE`,
   `RAG_CHUNK_OVERLAP`).
6. Pipeline integration: chunking runs after normalization; re-processing a
   document replaces its chunks (idempotent).
7. Chunk metadata: document title, language, filename (from Phase 2
   extraction) stored per chunk for later filtering (Phase 4).

## Invariants (unit-tested)

- Every chunk length ≤ `chunk_size` (in characters).
- Consecutive fixed-size chunks share exactly `overlap` characters (except
  the final chunk).
- Concatenation of fixed-size chunks minus overlaps reproduces the input.
- No empty chunks; whole input preserved for inputs ≤ `chunk_size`.
- `0 <= overlap < chunk_size` enforced at construction.

## Future work (documented, not implemented)

- **Semantic chunking** (embedding-similarity boundaries) — needs Phase 5
  embeddings; candidate for a later phase.
- **Parent-child chunking** (small chunks for retrieval pointing at larger
  parent windows for context) — schema supports it later via metadata.

## Acceptance Criteria

- [ ] Both chunkers pass boundary/overlap invariant tests.
- [ ] Worker persists chunks with metadata; re-run replaces them.
- [ ] Migration 0002 creates `chunks`; CI integration test proves the flow
  on Postgres. Gates green.
