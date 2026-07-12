# Architecture Overview

## System context

Four FastAPI microservices in a uv-workspace monorepo, one PostgreSQL
instance with pgvector, Gemini as the LLM provider (behind swappable
provider interfaces).

```mermaid
flowchart TB
    subgraph clients [Clients]
        U[User / API consumer]
    end
    subgraph platform [RAG Platform]
        ING[ingestion :8001]
        PROC[processing :8002]
        RET[retrieval :8003]
        GEN[generation :8004]
        PG[(PostgreSQL + pgvector)]
    end
    LLM[Gemini API]

    U -->|POST /documents| ING
    U -->|POST /query| GEN
    ING --> PG
    PROC --> PG
    RET --> PG
    GEN -->|HTTP| RET
    PROC --> LLM
    GEN --> LLM
```

## Data flow (ingest → answer)

```mermaid
sequenceDiagram
    participant C as Client
    participant I as ingestion
    participant DB as Postgres
    participant P as processing
    participant R as retrieval
    participant G as generation
    participant L as Gemini

    C->>I: POST /documents (file)
    I->>DB: insert document (dedup by content hash) + job
    P->>DB: poll job → normalize → chunk
    P->>L: embed chunks
    P->>DB: store chunks + vectors (pgvector)
    C->>G: POST /query {question}
    G->>R: POST /search {query}
    R->>DB: vector KNN + FTS → hybrid fusion
    R-->>G: ranked chunks
    G->>L: prompt with context
    L-->>G: answer
    G-->>C: answer + citations
```

## Storage

One shared Postgres instance in the MVP (ADR-0004). ORM models live in
`libs/db` (`rag_db`); the ingestion service owns the single alembic
migration lineage. Tables so far: `documents` (dedup by sha256 content
hash, per-filename versioning), `jobs` (outbox for async processing).

## Async processing

The `jobs` table is the queue (ADR-0005): ingestion enqueues transactionally
(outbox), the processing service claims with `FOR UPDATE SKIP LOCKED`,
retries up to `max_attempts`, then dead-letters (`dead`) and marks the
document `failed`. Pipeline: normalize (NFKC/whitespace) → metadata (title,
language heuristic, char/token counts) → chunk (Phase 3) → embed (Phase 5).

## Chunking

Own implementation (no LangChain): `FixedSizeChunker` (character windows +
overlap) and `RecursiveCharacterChunker` (paragraph → line → sentence →
word hierarchy, greedy merge, overlap carry). Strategy/size/overlap are
env-configurable (`RAG_CHUNK_*`). Chunks persist to the `chunks` table with
JSONB metadata (title, language, filename). Semantic and parent-child
chunking are documented future work.

## Metadata filtering

Chunk metadata is flat-string JSONB (keys today: `title`, `language`,
`filename`) with a `jsonb_path_ops` GIN index. `rag_contracts.filters`
defines `MetadataFilter` (`eq` / `in`, AND semantics); retrieval translates
filters to SQL predicates in `retrieval/filters.py`.

## Key decisions

See `docs/adr/`: monorepo+uv (0001), microservice boundaries (0002),
local-first/provider abstraction (0003), and later ADRs added per phase.
