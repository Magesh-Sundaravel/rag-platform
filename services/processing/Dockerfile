# --- builder -----------------------------------------------------------
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY libs ./libs
COPY services/processing ./services/processing
RUN uv sync --frozen --no-dev --package rag-processing

# --- runtime -----------------------------------------------------------
FROM python:3.12-slim
RUN useradd --create-home --uid 1000 app
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
USER app
EXPOSE 8002
CMD ["uvicorn", "processing.app:app", "--host", "0.0.0.0", "--port", "8002"]
