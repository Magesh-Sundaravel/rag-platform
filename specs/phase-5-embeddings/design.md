# Phase 5 Design

## `libs/providers` (`rag_providers`)

- `embedding.py` — protocol + `FakeEmbeddingProvider(dimension=768)`;
  vector = seeded `random.Random(sha256(text))` gaussians, L2-normalized.
- `gemini.py` — `GeminiEmbeddingProvider(model="gemini-embedding-001",
  dimension=768)`; lazy `genai.Client()` (reads `GEMINI_API_KEY`); async via
  `client.aio.models.embed_content`. Generation provider added in Phase 7 in
  the same module.
- `factory.py` — `build_embedding_provider(name, dimension)`.

Separate lib keeps `google-genai` out of `rag_common`, and lets both
processing (embed chunks) and retrieval (embed queries) share providers
without importing each other (ADR-0002/ADR-0006).

## Schema

`Chunk.embedding: Vector(768) | None` (pgvector SQLAlchemy type; stored as
text on SQLite where unit tests don't exercise vector search). Migration
0004: `CREATE EXTENSION IF NOT EXISTS vector`, add column, HNSW index
`USING hnsw (embedding vector_cosine_ops)`.

## Worker integration

`process_document(..., embedder)` embeds all chunk texts in one call and
assigns vectors before insert. Worker builds the provider at startup.

## llm-smoke workflow

`uv run pytest -m llm_smoke` with `GEMINI_API_KEY` from secrets; jobs are
skipped when the secret is absent (fork safety). Tests live under
`libs/providers/tests` (and later eval) marked `llm_smoke` and are
excluded from the default run via marker (`-m "not llm_smoke"` implicit:
tests skip when `GEMINI_API_KEY` unset).
