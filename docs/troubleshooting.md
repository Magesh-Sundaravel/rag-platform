# Troubleshooting

## `ModuleNotFoundError` for a service package in tests
Run `uv sync --all-packages` — plain `uv sync` installs only the (empty)
workspace root, not the members.

## pytest "import file mismatch" errors
Two test files share a basename (e.g. `test_health.py` in two services).
Rename to a unique basename (`test_<service>_health.py`).

## `docker compose up` fails on a service build
The Dockerfiles copy `uv.lock` from the repo root; run builds from the repo
root (compose already sets `context: .`). If the lock is stale:
`uv lock` then rebuild.

## Postgres port 5432 already in use
Another local Postgres is running. Either stop it or change the published
port in `docker-compose.yml` (`"15432:5432"`) and update your `.env`.

## Coverage gate fails after adding code
The gate is 90% (root `pyproject.toml`, `[tool.coverage.report]`). Add tests
for the new module — do not lower the gate.
