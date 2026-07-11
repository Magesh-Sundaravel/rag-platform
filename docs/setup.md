# Developer Setup

## Prerequisites

- [uv](https://docs.astral.sh/uv/) ≥ 0.5 (manages Python 3.12 automatically)
- Docker + Docker Compose
- `make`

## Steps

```bash
cp .env.example .env          # local config (never commit .env)
uv sync --all-packages        # creates .venv, installs all workspace members
uv run pre-commit install     # git hooks
make check                    # lint + typecheck + tests — must be green
make up                       # postgres + all services
```

Verify: `curl localhost:8001/health` … `:8004/health` all return
`{"status":"ok","service":"<name>"}`.

## Everyday commands

| Command | Purpose |
|---|---|
| `make fmt` | auto-fix lint + format |
| `make lint` / `make typecheck` / `make test` | individual gates |
| `make check` | all gates (run before every commit) |
| `make up` / `make down` | local stack |
| `uv add <pkg> --package rag-<svc>` | add a dependency to one service |

## Repository conventions

- Specs first: no implementation without `specs/phase-N-*/spec.md`.
- Decisions go in `docs/adr/` (sequential numbering).
- Tests live next to the code they test (`libs/*/tests`, `services/*/tests`);
  test files need unique basenames across the repo (pytest rootdir constraint).
