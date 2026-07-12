# Phase 7 Design

## Contracts (`rag_contracts.generation`)

- `QueryRequest(question [1..2000], top_k = 5 [1..20],
  filters: list[MetadataFilter] = [])`
- `Citation(chunk_id, document_id, snippet)`
- `Usage(prompt_tokens: int, completion_tokens: int)`
- `QueryResponse(answer: str, citations: list[Citation], usage: Usage)`

## Providers (`rag_providers.generation`, `rag_providers.gemini`)

```python
@dataclass
class GenerationResult:
    text: str
    prompt_tokens: int
    completion_tokens: int

class GenerationProvider(Protocol):
    async def generate(self, prompt: str) -> GenerationResult: ...
```

- `FakeGenerationProvider`: finds `[n] <text>` context-block lines in the
  prompt and answers `"Based on the provided context [1][2]...: <first
  context line>"`; empty-context prompts get an honest "no context"
  answer. Token counts = word counts (deterministic, offline).
- `GeminiGenerationProvider(model="gemini-2.5-flash")`: async
  `generate_content`; usage from `response.usage_metadata`.
- `rag_providers.factory.build_generation_provider(name)` mirrors the
  existing `build_embedding_provider` factory.

## Generation service

- `generation/retrieval_client.py` -- `RetrievalClient(base_url, timeout,
  retries, transport=None)` using `httpx.AsyncClient`; POST `/search` with
  `rag_contracts.search` models; retries on 5xx and transport errors only
  (client errors propagate immediately); raises `UpstreamError` after
  exhausting retries. `transport` is injectable for tests
  (`httpx.MockTransport`), matching the `client=` pattern already used by
  `GeminiEmbeddingProvider`.
- `generation/prompting.py` -- `build_prompt(question, chunks)` (numbered
  context blocks + citation instructions) and
  `extract_citations(answer, chunks)` mapping `[n]` -> chunk refs (dedup,
  order of first appearance, snippet = first 200 chars).
- `generation/routes.py` -- `POST /query` orchestration: search, short
  circuit on empty results, else build prompt -> generate -> extract
  citations.
- Settings: `retrieval_url` (default `http://localhost:8003`),
  `generation_provider` (fake/gemini), `request_timeout_seconds`,
  `retrieval_retries`.

## Boundary note

Generation <-> retrieval is HTTP only (ADR-0002): no shared DB access from
the generation service; payloads are `rag_contracts.search` models.
