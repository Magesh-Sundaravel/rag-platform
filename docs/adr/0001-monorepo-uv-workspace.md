# ADR-0001: Monorepo with uv workspace

- **Status:** Accepted
- **Date:** 2026-07-11

## Context

The platform consists of four deployable services plus shared libraries. We
must choose between one repository per service (polyrepo) or a single
repository (monorepo), and how to manage Python dependencies across them.

## Decision

Single monorepo. Dependency management via a uv workspace: every service and
library is a workspace member with its own `pyproject.toml`; one `uv.lock` at
the root guarantees consistent versions everywhere; shared tool configuration
(Ruff, mypy, pytest, coverage) lives once in the root `pyproject.toml`.

## Consequences

- Atomic cross-service changes (contract + producer + consumer in one PR).
- One CI pipeline; no config drift between services.
- Services still build into independent Docker images (`uv sync --package`).
- Trade-off: repo grows large over time; acceptable at this scale.
