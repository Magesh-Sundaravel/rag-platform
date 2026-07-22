# Phase 8 Design

## Contracts (`rag_contracts.evaluation`)

- `EvalExample(question: str, contexts: list[str], answer: str, ground_truth: str)`
- `MetricScores(faithfulness, answer_relevancy, context_precision, context_recall: float)`
- `EvalResult(example: EvalExample, scores: MetricScores)`
- `EvaluationReport(results: list[EvalResult], averages: MetricScores)`

## `rag_evaluation` lib

- `judging.py`:
  - `_score_from_judge(prompt: str, judge: GenerationProvider) -> float` —
    calls `judge.generate(prompt)`, extracts the first float via regex,
    clamps to `[0, 1]`; returns `0.0` if no float is found.
  - Judge prompts are single-purpose, plain-text, and instruct: *"Respond
    with only a number between 0.0 and 1.0 on the first line."*
- `metrics.py`:
  - `faithfulness(answer, contexts, judge)`
  - `answer_relevancy(question, answer, judge)`
  - `context_precision(question, contexts, judge)`
  - `context_recall(contexts, ground_truth, judge)`
  - Each builds its judge prompt and delegates scoring to
    `_score_from_judge`.
- `runner.py`:
  - `evaluate(examples, judge) -> EvaluationReport`: runs the four metrics
    per example (`asyncio.gather` per example), builds `EvalResult`s, and
    averages each metric across the dataset.
- `golden.py`: the 3-example fixture dataset (module-level constant,
  imported by both the unit test and the llm-smoke test so they can't
  drift apart).

## Judge abstraction

No new protocol: the judge parameter is typed `GenerationProvider` (from
`rag_providers.generation`), the same protocol used for answer generation
in Phase 7. `build_generation_provider("bedrock")` builds the real judge;
tests use a module-local `StubJudge` (implements `generate` by returning a
canned `GenerationResult`), not `FakeGenerationProvider` — that fake is
purpose-built for citation-echoing, not score output.

## Boundary note

`rag_evaluation` depends only on `rag_contracts` and `rag_providers`; it is
a library, not a service (no port, no HTTP surface) — invoked from tests
and, later, an offline eval script if needed.
