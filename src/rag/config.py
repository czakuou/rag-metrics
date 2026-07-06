"""Central application configuration via Pydantic Settings."""

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

from rag.shared.types import ChunkStrategy


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LLM — routed through the LiteLLM proxy, see shared/llm.py
    openai_api_key: str = "sk-openai-local-dev"
    litellm_base_url: str = "http://litellm:4000"
    litellm_master_key: str = "sk-litellm-local-dev"
    llm_chat_model: str = "default-chat"
    llm_embed_model: str = "default-embedding"
    llm_eval_model: str = "eval-judge"

    # Ingestion
    chunking_strategy: ChunkStrategy = ChunkStrategy.FIXED

    # Vector store backend — swap via .env. Supported values are the keys of
    # backends.vectorstore.factory._REGISTRY.
    vectorstore_backend: str = "pgvector"
    database_url: PostgresDsn = PostgresDsn("postgresql://rag:rag@localhost:5432/rag")

    # Retrieval
    retrieval_k: int = 10
    retrieval_relevance_threshold: float = 0.5

    # Evals — CI gate thresholds
    eval_faithfulness_threshold: float = 0.85
    eval_answer_relevancy_threshold: float = 0.85
    eval_context_precision_threshold: float = 0.85

    # Evals — max allowed drop vs. data/baseline_scores.json before the CI gate fails,
    # even if the metric is still above its absolute threshold. Tolerates RAGAS judge
    # noise without masking a real regression.
    eval_regression_tolerance: float = 0.02

    # Agent — ReAct loop
    agent_max_iterations: int = 5


settings = Settings()
