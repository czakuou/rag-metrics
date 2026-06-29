"""Central application configuration via Pydantic Settings."""

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LLM — routed through the LiteLLM proxy, see shared/llm.py
    openai_api_key: str
    litellm_base_url: str = "http://litellm:4000"
    litellm_master_key: str = "sk-litellm-local-dev"
    llm_chat_model: str = "default-chat"
    llm_embed_model: str = "default-embedding"
    llm_eval_model: str = "eval-judge"

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

    # Agent — ReAct loop
    agent_max_iterations: int = 5


settings = Settings()
