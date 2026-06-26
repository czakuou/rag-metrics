"""Central application configuration via Pydantic Settings."""

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LLM
    openai_api_key: str
    llm_model: str = "gpt-4o-mini"

    # Embedding backend — swap via .env
    embedding_backend: str = "openai"  # "openai" | "bge"
    embedding_model: str = "text-embedding-3-small"

    # Vector store
    database_url: PostgresDsn

    # Evals — CI gate thresholds
    eval_faithfulness_threshold: float = 0.70
    eval_answer_relevancy_threshold: float = 0.65
    eval_context_precision_threshold: float = 0.65


settings = Settings()
