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

## Key decisions

See `docs/adr/`: monorepo+uv (0001), microservice boundaries (0002),
local-first/provider abstraction (0003), and later ADRs added per phase.
