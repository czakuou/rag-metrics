"""Central LLM gateway. All chat/embedding calls route through the LiteLLM proxy.

This is the only place `litellm` is imported outside of `backends/embedding/`.
"""

from typing import Any

import litellm
import structlog

from rag.config import settings

logger = structlog.get_logger(__name__)


def complete(messages: list[dict[str, str]], model: str, **kwargs: Any) -> str:
    try:
        response = litellm.completion(
            model=model,
            messages=messages,
            api_base=settings.litellm_base_url,
            api_key=settings.litellm_master_key,
            **kwargs,
        )
    except Exception:
        logger.error("llm_completion_failed", model=model)
        raise

    cost = litellm.completion_cost(completion_response=response)
    logger.info(
        "llm_completion",
        model=model,
        prompt_tokens=response.usage.prompt_tokens,
        completion_tokens=response.usage.completion_tokens,
        cost_usd=cost,
    )
    return str(response.choices[0].message.content)


def embed(texts: list[str], model: str, **kwargs: Any) -> list[list[float]]:
    try:
        response = litellm.embedding(
            model=model,
            input=texts,
            api_base=settings.litellm_base_url,
            api_key=settings.litellm_master_key,
            **kwargs,
        )
    except Exception:
        logger.error("llm_embedding_failed", model=model)
        raise

    cost = litellm.completion_cost(completion_response=response)
    logger.info(
        "llm_embedding",
        model=model,
        num_texts=len(texts),
        cost_usd=cost,
    )
    return [item["embedding"] for item in response.data]
