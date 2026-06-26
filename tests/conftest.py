"""Shared pytest fixtures."""

from collections.abc import Generator

import pytest
from testcontainers.postgres import PostgresContainer

from rag.config import Settings


@pytest.fixture
def test_settings() -> Settings:
    """Override settings for tests — no real API keys needed."""
    return Settings(
        openai_api_key="sk-test",
        database_url="postgresql+asyncpg://rag:test@localhost:5432/rag_test",
    )


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer]:
    """Spin up a real pgvector-enabled Postgres for tests that need a live database."""
    with PostgresContainer("pgvector/pgvector:pg16") as container:
        yield container
