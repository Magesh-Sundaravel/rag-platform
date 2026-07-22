# Phase 0 Specification: Project Foundation

- **Status:** DRAFT — awaiting approval
- **Author:** Claude (Principal AI Engineer role), for Magesh
- **Date:** 2026-07-11
- **Phase:** 0 of 10

---

## 1. Problem Statement

We are building a production-grade RAG platform intended to scale from MVP to
10M+ documents. Before any feature code is written, we need a foundation that
makes every later phase cheaper: a repository layout that supports multiple
independently deployable services, reproducible environments, enforced code
quality, and CI that fails fast. Phase 0 produces **zero RAG functionality**
on purpose — its output is the skeleton every other phase builds on.

## 2. Decisions Already Made (from kickoff Q&A)

| Decision | Choice | Rationale |
|---|---|---|
| Service structure | Microservices from day 1, in a **monorepo** | Portfolio demonstrates distributed systems; monorepo keeps tooling/CI/contracts unified |
| Cloud timing | Local-first; provider-backed LLM access when needed; full infra deferred to Phase 10 | Fast feedback, near-zero cost during development |
| Cloud status | No production cloud environment yet | Infrastructure setup deferred until deployment phase |
| Python | 3.12 | Mature wheel/SDK support across the ML ecosystem |

## 3. Goals

1. A monorepo where four services can be developed, tested, and containerized
   independently while sharing contracts and utilities.
2. One-command local environment: `docker compose up` brings up
   Postgres+pgvector and all service containers.
3. One-command developer setup: `uv sync` at the root installs everything.
4. CI that runs lint, format check, type check, tests+coverage, and Docker
   builds on every push/PR.
5. Pre-commit hooks so broken code rarely reaches CI.
6. Documentation structure (README, ADRs, architecture docs) in place with
   the first three ADRs written.

## 4. Non-Goals (explicitly out of scope for Phase 0)

- Any RAG functionality (upload, parsing, chunking, embedding, retrieval, generation).
- Inter-service communication (HTTP clients, queues) — the *decision* is recorded in an ADR, the implementation lands in Phase 2.
- Database schemas/migrations (Phase 1).
- Terraform, ECS/EKS, RDS, or any production cloud resource (Phase 10 deployment work).
- Authentication/authorization (Phase 4).
- Kubernetes manifests.

## 5. Architecture

### 5.1 Services (skeletons only in Phase 0)

| Service | Port | Responsibility (future) | Phase 0 content |
|---|---|---|---|
| `ingestion` | 8001 | Document upload, parsing, dedup, versioning | FastAPI app with `/health`, `/ready` |
| `processing` | 8002 | Async pipeline: normalization, chunking, embedding | Same skeleton (becomes a worker in Phase 2) |
| `retrieval` | 8003 | Vector/BM25/hybrid search, reranking | Same skeleton |
| `generation` | 8004 | Bedrock generation, prompts, citations, memory | Same skeleton |

Each service: its own `pyproject.toml` (uv workspace member), own
`Dockerfile`, own `tests/`. Each exposes `GET /health` (liveness, always 200)
and `GET /ready` (readiness; in Phase 0 always 200, later checks DB etc.).

### 5.2 Shared libraries (uv workspace members, never deployed alone)

| Library | Contents |
|---|---|
| `libs/common` | Settings base (pydantic-settings, env-driven), structured logging setup, exception hierarchy, FastAPI app factory (wires health endpoints, logging middleware) |
| `libs/contracts` | Pydantic models shared across service boundaries (empty placeholder in Phase 0 — filled per phase) |

Rule: services may import `libs/*`; services may **never** import each other.
Enforced later with import-linter; documented in ADR-0002 now.

### 5.3 Repository layout

```
rag-platform/
├── .github/workflows/ci.yml
├── services/
│   ├── ingestion/
│   │   ├── pyproject.toml
│   │   ├── Dockerfile
│   │   ├── src/ingestion/          # app.py, config.py
│   │   └── tests/
│   ├── processing/   (same shape)
│   ├── retrieval/    (same shape)
│   └── generation/   (same shape)
├── libs/
│   ├── common/
│   │   ├── pyproject.toml
│   │   ├── src/rag_common/
│   │   └── tests/
│   └── contracts/    (same shape, src/rag_contracts/)
├── specs/                          # Spec Kit artifacts, one dir per phase
│   └── phase-0-foundation/
│       ├── spec.md                 # this file
│       ├── design.md               # written after spec approval
│       └── tasks.md                # task breakdown
├── docs/
│   ├── architecture/overview.md    # system diagram (Mermaid)
│   ├── adr/                        # ADR-0001..0003
│   ├── setup.md                    # developer onboarding
│   └── troubleshooting.md
├── docker-compose.yml              # postgres+pgvector, 4 services
├── pyproject.toml                  # uv workspace root + shared tool config
├── uv.lock
├── .pre-commit-config.yaml
├── .env.example
├── Makefile                        # dev, test, lint, typecheck, up, down
└── README.md
```

### 5.4 Tooling configuration

- **uv workspace**: root `pyproject.toml` declares `[tool.uv.workspace]`
  members `services/*`, `libs/*`. Single `uv.lock` for the whole repo.
- **Ruff**: lint + format, configured once at root. Rule set: `E,F,W,I,N,UP,B,SIM,C4,RUF` plus `D` (pydocstyle, Google convention) on `src/`, relaxed in `tests/`.
- **mypy**: strict mode (`strict = true`) on all `src/` code.
- **pytest**: root config; `pytest-cov` with coverage gate **≥ 90%** (trivial now, keeps us honest later); `pytest-asyncio` in auto mode.
- **pre-commit**: ruff (lint+format), `uv lock --check`, end-of-file/trailing-whitespace, YAML check.
- **Docker**: one multi-stage Dockerfile per service (uv-based builder → slim runtime, non-root user). Postgres image: `pgvector/pgvector:pg16`.

### 5.5 CI pipeline (GitHub Actions)

Triggers: push to `main`, all PRs.

```
lint (ruff check + format --check)
typecheck (mypy)
test (pytest + coverage gate, all workspace members)
docker-build (matrix over 4 services; build only, no push)
```

Jobs run in parallel where independent; `docker-build` uses layer caching.
Pushing images to ECR is Phase 10.

## 6. ADRs to be written in this phase

1. **ADR-0001**: Monorepo with uv workspace for a multi-service platform.
2. **ADR-0002**: Microservices from day 1; service boundary and import rules.
3. **ADR-0003**: Local-first development; production cloud deferred until deployment work.

## 7. Testing Strategy for Phase 0

TDD applies even to skeletons:

- Unit tests for `libs/common`: settings loading from env, app factory
  produces an app whose `/health` and `/ready` return 200 (via `httpx.AsyncClient`).
- Per-service API tests: `/health` and `/ready` contract (status code + body shape).
- CI is the integration test of the tooling itself: the phase is not done
  until the pipeline is green on GitHub.

## 8. Acceptance Criteria (Definition of Done)

- [ ] `git init` done; repo pushed to GitHub with `main` protected mindset (PR-based flow from Phase 1 on).
- [ ] `uv sync` from a clean clone succeeds and installs all workspace members.
- [ ] `make lint`, `make typecheck`, `make test` all pass locally.
- [ ] Coverage ≥ 90% on existing code.
- [ ] `docker compose up` starts Postgres and all four services; all `/health` endpoints return 200.
- [ ] `pre-commit run --all-files` passes.
- [ ] GitHub Actions pipeline green on `main`.
- [ ] README covers: what the project is, architecture sketch, quickstart (< 5 commands), phase roadmap.
- [ ] ADR-0001..0003 written; `docs/setup.md` lets a stranger get running.

## 9. Risks & Open Questions

- **Risk:** 4 service skeletons + 2 libs is boilerplate-heavy; mitigated by the shared app factory in `libs/common` (each service's `app.py` stays ~10 lines).
- **Risk:** strict mypy from day 0 adds friction; accepted deliberately — retrofitting strictness is far more painful.
- **Open question (needs answer at approval time):** GitHub repo name — proposal: `rag-platform`. Public from day 1 (it's a portfolio piece)?

## 10. What Happens After Approval

Per Spec Kit workflow: `design.md` (concrete file contents/interfaces) →
`tasks.md` (ordered task list with verify steps) → TDD implementation →
validation against §8 → docs → review → phase completion checklist.
