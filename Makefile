.PHONY: install lint fmt typecheck test check up down

install:
	uv sync --all-packages

lint:
	uv run ruff check .
	uv run ruff format --check .

fmt:
	uv run ruff check --fix .
	uv run ruff format .

typecheck:
	uv run mypy .

test:
	uv run pytest --cov

check: lint typecheck test

up:
	docker compose up -d --build

down:
	docker compose down
