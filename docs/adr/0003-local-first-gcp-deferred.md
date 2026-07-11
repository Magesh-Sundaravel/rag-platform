# ADR-0003: Local-first development; GCP deferred

- **Status:** Accepted
- **Date:** 2026-07-11

## Context

No GCP project exists yet. Cloud resources cost money and slow the feedback
loop during early development.

## Decision

Develop everything locally with Docker Compose (Postgres+pgvector). LLM
access is abstracted behind provider interfaces with deterministic fake
implementations so the entire pipeline is testable offline; real Gemini
providers (google-genai SDK) ship alongside and activate when
`GEMINI_API_KEY` (or Vertex AI ADC) is configured. Full GCP infrastructure
(Terraform, GKE, Cloud SQL, Artifact Registry) is written in Phase 10 and
deployed when a billing-enabled project exists.

## Consequences

- Zero cloud cost until deployment; instant local iteration.
- Real-LLM code paths remain unverified until a key is provided — flagged in
  PROJECT_STATUS.md as explicit technical debt.
- Provider abstraction doubles as good architecture (swappable models,
  testability) rather than pure scaffolding.
