# Phase 0 Tasks

| # | Task | Verify | Status |
|---|------|--------|--------|
| 1 | git init, .gitignore, root pyproject (workspace + tool config) | `uv sync` succeeds | done |
| 2 | libs/common: tests first, then config/logging/exceptions/app_factory | `pytest libs/common` green | done |
| 3 | libs/contracts placeholder | imports | done |
| 4 | 4 service skeletons (tests first: health contract) | `pytest` green all members | done |
| 5 | Ruff + mypy strict pass on all code | `make lint typecheck` | done |
| 6 | Dockerfiles x4 + docker-compose (pgvector) | compose up, curl /health x4 | done |
| 7 | Makefile, .env.example, pre-commit | `pre-commit run --all-files` | done |
| 8 | CI workflow | pipeline green on GitHub | done |
| 9 | Docs: README, ADR-0001..3, setup, troubleshooting, architecture | review | done |
| 10 | PROJECT_STATUS.md + commits + push | git log clean | done |
