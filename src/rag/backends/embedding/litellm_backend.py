"""LiteLLM-backed embedding backend. Provider selection lives in litellm proxy config."""

from rag.backends.embedding.protocol import EmbedFn
from rag.shared.llm import embed as llm_embed


def make_litellm_backend(model: str, base_url: str, api_key: str) -> EmbedFn:
    def embed(texts: list[str]) -> list[list[float]]:
        return llm_embed(texts, model=model)

    return embed
