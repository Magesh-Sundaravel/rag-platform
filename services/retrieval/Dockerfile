# --- builder -----------------------------------------------------------
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY libs ./libs
COPY services/retrieval ./services/retrieval
RUN uv sync --frozen --no-dev --package rag-retrieval

# --- runtime -----------------------------------------------------------
FROM python:3.12-slim
RUN useradd --create-home --uid 1000 app
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
USER app
EXPOSE 8003
CMD ["uvicorn", "retrieval.app:app", "--host", "0.0.0.0", "--port", "8003"]
