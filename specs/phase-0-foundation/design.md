# Phase 0 Design: Project Foundation

- **Status:** APPROVED (autonomous mode; spec approved by proxy 2026-07-11)
- **Spec:** [spec.md](./spec.md)

## 1. Workspace layout

Exactly as spec §5.3. Root `pyproject.toml` is a non-buildable virtual
workspace root (`[tool.uv.workspace] members = ["services/*", "libs/*"]`)
holding all shared tool config (ruff, mypy, pytest, coverage).

Package naming: libraries import as `rag_common` and `rag_contracts`;
services import as `ingestion`, `processing`, `retrieval`, `generation`.

## 2. libs/common — public interface

```
rag_common/
├── config.py      # BaseServiceSettings(BaseSettings): service_name, environment,
│                  #   log_level, host, port; env prefix "RAG_", .env support
├── logging.py     # configure_logging(settings) -> None; structlog JSON in prod,
│                  #   pretty console in dev; stdlib logging routed through structlog
├── exceptions.py  # RagPlatformError(Exception) base with .code and .detail;
│                  #   NotFoundError, ValidationError_, ConflictError, UpstreamError
└── app_factory.py # create_app(settings, *, title, version, lifespan=None) -> FastAPI
                   #   - mounts GET /health -> {"status": "ok", "service": name}
                   #   - mounts GET /ready  -> {"status": "ready"} (hookable later)
                   #   - registers exception handler mapping RagPlatformError -> JSON
                   #   - request-logging middleware (method, path, status, duration_ms)
```

Dependencies: `fastapi`, `pydantic-settings`, `structlog`.

## 3. libs/contracts

`rag_contracts/__init__.py` only (placeholder + version). Models land per phase.

## 4. Service skeleton (identical shape x4)

```
services/<name>/
├── pyproject.toml           # depends on rag-common (workspace), uvicorn
├── Dockerfile               # multi-stage: uv sync --frozen -> python:3.12-slim, non-root
├── src/<name>/
│   ├── __init__.py
│   ├── config.py            # Settings(BaseServiceSettings) with service defaults (port)
│   └── app.py               # settings = Settings(); app = create_app(settings, ...)
└── tests/test_health.py     # /health and /ready contract tests via httpx ASGI transport
```

## 5. Docker

- Per-service Dockerfile, multi-stage:
  1. `ghcr.io/astral-sh/uv:python3.12-bookworm-slim` builder; `uv sync --frozen
     --no-dev --package <name>` (workspace-aware; copies libs + service).
  2. `python:3.12-slim` runtime, copies venv, `USER app`, `CMD uvicorn <name>.app:app`.
- `docker-compose.yml`: `postgres` (pgvector/pgvector:pg16, healthcheck,
  volume) + 4 services with build contexts at repo root, env from `.env`.

## 6. CI (.github/workflows/ci.yml)

Jobs: `lint` (ruff check + format --check), `typecheck` (mypy), `test`
(pytest --cov, gate 90%), `docker-build` (matrix over services, buildx with
GHA cache, no push). All on push to main + PRs. uv installed via
`astral-sh/setup-uv`.

## 7. Quality gate configs

- Ruff: line-length 100, target py312, rules `E,F,W,I,N,UP,B,SIM,C4,RUF,D`;
  `D` Google convention; ignore `D1xx` in tests; `__init__.py` exempt from D104.
- mypy: strict, per-package `mypy_path` via uv-installed packages; pydantic plugin.
- pytest: `asyncio_mode = "auto"`, testpaths discovered per workspace member;
  coverage source = all `src/` dirs.
- pre-commit: ruff, ruff-format, uv-lock check, standard hygiene hooks.

## 8. Make targets

`make install | lint | fmt | typecheck | test | check (lint+typecheck+test) | up | down`

## 9. Verification plan

1. `uv sync` clean → 2. `make check` green → 3. `docker compose up -d` →
   curl all 4 `/health` → 4. `pre-commit run --all-files` → 5. push, CI green.
