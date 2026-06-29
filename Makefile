.PHONY: install generate ingest eval agent typecheck test lint format pre-commit up down

install:
	uv sync
	uv run pre-commit install

generate:
	uvx baml-cli generate --from src/rag/agent/baml_src/

up:
	docker compose up -d

down:
	docker compose down

ingest:
	uv run python -m rag.ingestion.pipeline

eval:
	uv run pytest -m integration tests/evals/test_golden_dataset.py -v

agent:
	uv run python -m rag.agent.pipeline

typecheck: generate
	uv run mypy src/

lint:
	uv run ruff check src/ tests/

format:
	uv run ruff format src/ tests/

test: generate
	uv run pytest tests/ -v

pre-commit:
	uv run pre-commit run --all-files
