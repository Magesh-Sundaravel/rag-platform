# --- builder -----------------------------------------------------------
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY libs ./libs
COPY services/ingestion ./services/ingestion
RUN uv sync --frozen --no-dev --package rag-ingestion

# --- runtime -----------------------------------------------------------
FROM python:3.12-slim
RUN useradd --create-home --uid 1000 app
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY services/ingestion/alembic ./services/ingestion/alembic
COPY services/ingestion/alembic.ini ./services/ingestion/alembic.ini
ENV PATH="/app/.venv/bin:$PATH"
USER app
EXPOSE 8001
CMD ["uvicorn", "ingestion.app:app", "--host", "0.0.0.0", "--port", "8001"]
