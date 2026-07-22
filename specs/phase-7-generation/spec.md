# Phase 7 Specification: Generation with Citations

- **Status:** Accepted
- **Date:** 2026-07-12
- **Phase:** 7 of 10

## Problem

Phase 6 gave the platform a hybrid search API, but nothing yet answers a
question in natural language. The generation service needs to turn
retrieved chunks into a grounded answer with verifiable citations, over a
real service boundary (generation -> retrieval via HTTP, per ADR-0002).

## Scope

1. `GenerationProvider` protocol in `rag_providers`: `async generate(prompt)
   -> GenerationResult {text, prompt_tokens, completion_tokens}`.
2. `FakeGenerationProvider`: deterministic; echoes the numbered context
   block ids it sees (`[1] [2] ...`) so citation extraction is fully
   testable offline.
3. `BedrockGenerationProvider`: `amazon.nova-micro-v1:0` via Bedrock
   Converse API; maps Bedrock token usage.
4. `POST /query` on the generation service: `{question, top_k, filters?}`:
   - calls retrieval `POST /search` over HTTP (httpx, configurable
     timeout, retries with backoff on 5xx/transport errors),
   - builds a grounded prompt with numbered context blocks
     (`[1] <chunk text>`), instructing bracket citations,
   - parses `[n]` markers from the answer into citations,
   - returns `{answer, citations: [{chunk_id, document_id, snippet}],
     usage: {prompt_tokens, completion_tokens}}`.
5. No retrieved context -> the service answers honestly that nothing was
   found (no LLM call), empty citations.

## Out of scope (later phases)

- Conversation memory / multi-turn context (roadmap mentions "memory"
  under Phase 7, but is deferred; this phase is single-turn Q&A).
- RAGAS evaluation of answer quality (Phase 8).

## Testing

- Prompt builder + citation parser: pure unit tests.
- API: mocked retrieval HTTP transport (`httpx.MockTransport`), fake
  generation provider.
- Retry behavior: mock transport with a stateful handler (5xx then
  success).
- Real Bedrock generation: llm-smoke test.

## Acceptance Criteria

- [x] `/query` returns a grounded answer with citations mapped to chunk ids.
- [x] Retrieval outage -> 502 upstream error envelope after retries.
- [x] No retrieved context -> honest "not found" answer, no LLM call.
- [x] llm-smoke generates a real answer.
- [x] Gates green.
