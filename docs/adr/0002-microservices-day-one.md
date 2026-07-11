# ADR-0002: Microservices from day 1 with strict boundary rules

- **Status:** Accepted
- **Date:** 2026-07-11

## Context

The owner explicitly chose microservices from day 1 over a modular monolith
(kickoff decision), accepting higher early complexity in exchange for a
genuinely distributed architecture.

## Decision

Four services — ingestion, processing, retrieval, generation — each
independently containerized and deployable. Boundary rules:

1. A service may import `libs/common` and `libs/contracts`, never another service.
2. Cross-service communication is HTTP (sync) or the Postgres job queue (async).
3. Data exchanged across boundaries uses models from `libs/contracts` only.
4. Each service owns its tables; other services access foreign data through
   the owning service's API — with a pragmatic MVP exception recorded in
   ADR-0005 (shared database instance).

## Consequences

- Real distributed-system concerns (timeouts, retries, partial failure) exist
  from Phase 2 onward; this is intentional.
- The shared app factory keeps per-service boilerplate minimal.
- Boundary rule 1 will be enforced with import-linter once services grow.
