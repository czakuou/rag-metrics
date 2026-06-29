"""Central application configuration via Pydantic Settings."""

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LLM
    openai_api_key: str
    llm_model: str = "gpt-4o-mini"

    # Embedding backend — swap via .env. Supported values are the keys of
    # backends.embedding.factory._REGISTRY.
    embedding_backend: str = "openai"
    embedding_model: str = "text-embedding-3-small"

    # Ingestion
    chunking_strategy: str = "fixed"

    # Vector store backend — swap via .env. Supported values are the keys of
    # backends.vectorstore.factory._REGISTRY.
    vectorstore_backend: str = "pgvector"
    database_url: PostgresDsn

    # Retrieval
    retrieval_k: int = 10
    retrieval_relevance_threshold: float = 0.5

    # Evals — CI gate thresholds
    eval_faithfulness_threshold: float = 0.70
    eval_answer_relevancy_threshold: float = 0.65
    eval_context_precision_threshold: float = 0.65


settings = Settings()
