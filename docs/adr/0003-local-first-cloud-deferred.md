# ADR-0003: Local-first development; production cloud deferred

- **Status:** Accepted
- **Date:** 2026-07-11

## Context

No production cloud environment exists yet. Cloud resources cost money and slow the feedback
loop during early development.

## Decision

Develop everything locally with Docker Compose (Postgres+pgvector). LLM
access is abstracted behind provider interfaces with deterministic fake
implementations so the entire pipeline is testable offline; real Bedrock
providers (`boto3` SDK) ship alongside and activate when AWS credentials and
region are configured. Production cloud infrastructure is written in
Phase 10 and deployed only after the target platform is selected and funded.

## Consequences

- Zero cloud cost until deployment; instant local iteration.
- Real-LLM code paths remain unverified until a key is provided — flagged in
  PROJECT_STATUS.md as explicit technical debt.
- Provider abstraction doubles as good architecture (swappable models,
  testability) rather than pure scaffolding.
