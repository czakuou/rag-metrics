.PHONY: install ingest eval agent typecheck test lint format pre-commit up down

install:
	uv sync
	uv run pre-commit install

up:
	docker compose up -d

down:
	docker compose down

ingest:
	uv run python -m rag.ingestion.pipeline

eval:
	uv run python -m rag.evals.pipeline

agent:
	uv run python -m rag.agent.pipeline

typecheck:
	uv run mypy src/

lint:
	uv run ruff check src/ tests/

format:
	uv run ruff format src/ tests/

test:
	uv run pytest tests/ -v

pre-commit:
	uv run pre-commit run --all-files
