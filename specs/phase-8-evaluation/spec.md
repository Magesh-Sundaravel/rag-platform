# Phase 8 Specification: RAGAS Evaluation Framework

- **Status:** Accepted
- **Date:** 2026-07-12
- **Phase:** 8 of 10

## Problem

Phases 6-7 gave the platform a working retrieve-then-generate pipeline, but
nothing measures answer quality. We need a lightweight evaluation harness
that scores the standard RAGAS metrics against a golden dataset, without
adopting the `ragas` package's own LLM-integration layer (see ADR-0007).

## Scope

1. `rag_evaluation` lib:
   - `EvalExample` contract: `question`, `contexts: list[str]`, `answer`,
     `ground_truth: str`.
   - `faithfulness(answer, contexts, judge) -> float`: is the answer
     supported by the given contexts?
   - `answer_relevancy(question, answer, judge) -> float`: does the answer
     address the question?
   - `context_precision(question, contexts, judge) -> float`: are the
     retrieved contexts relevant to the question?
   - `context_recall(contexts, ground_truth, judge) -> float`: is the
     ground-truth answer's content covered by the retrieved contexts?
   - Each metric sends one judge prompt requesting a single `0.0`-`1.0`
     score and a one-line reason; the response is parsed defensively
     (regex for the first float in range, clamped, defaults to `0.0` on a
     malformed response).
   - `evaluate(examples: list[EvalExample], judge: GenerationProvider) ->
     EvaluationReport`: runs all four metrics per example, returns
     per-example scores plus dataset averages.
2. A 3-example golden dataset (fixture data, checked in) covering: a fully
   supported answer, a partially unsupported answer (hallucination), and
   an irrelevant-context case.
3. `llm_smoke`-marked test: runs `evaluate()` over the golden dataset with
   the real `BedrockGenerationProvider` as judge; asserts scores land in
   `[0, 1]` and the fully-supported example scores higher on faithfulness
   than the hallucination example.

## Out of scope

- Full upstream-RAGAS statement-level decomposition (ADR-0007).
- A persisted eval-results store / dashboard (may follow in a later phase
  if needed).
- Wiring evaluation into CI as a blocking gate (LLM-gated, advisory only
  for now).

## Testing

- Metric scoring/parsing: unit tests with a deterministic `StubJudge`
  double covering well-formed and malformed judge responses.
- `evaluate()` aggregation: unit test with a stub judge over the golden
  dataset shape.
- Real-judge run: llm-smoke test (secret-gated, self-skips otherwise).

## Acceptance Criteria

- [x] All four metrics return values in `[0, 1]` for well-formed judge
      output and degrade gracefully (score `0.0`) on malformed output.
- [x] `evaluate()` produces per-example scores and correct averages.
- [x] llm-smoke run scores the golden dataset with real Bedrock and the
      hallucination example scores lower on faithfulness than the
      fully-supported one.
- [x] Gates green.
