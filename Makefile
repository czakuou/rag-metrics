.PHONY: install generate ingest eval agent typecheck test lint format pre-commit up down logs-llm

install:
	uv sync
	uv run pre-commit install

generate:
	uvx baml-cli generate --from src/rag/agent/baml_src/

# Brings up postgres, the LiteLLM proxy, and the app — all LLM calls route through litellm.
up:
	docker compose up -d

down:
	docker compose down

logs-llm:
	docker compose logs litellm -f

# Local (non-containerized) runs talk to postgres/litellm via the docker port mappings on
# localhost, since the host can't resolve the "postgres"/"litellm" service names from .env.
LOCAL_ENV := DATABASE_URL=postgresql+asyncpg://rag:changeme@localhost:5432/rag_db \
	LITELLM_BASE_URL=http://localhost:4000

ingest:
	$(LOCAL_ENV) uv run python -m rag.ingestion.pipeline

eval:
	$(LOCAL_ENV) uv run pytest -m integration tests/evals/test_golden_dataset.py -v

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
