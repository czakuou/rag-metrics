"""LiteLLM-backed embedding backend.

Provider selection lives in litellm proxy config; the proxy URL and key are read
by `rag.shared.llm.embed` from `Settings` itself, not passed through this factory.
"""

from rag.backends.embedding.protocol import EmbedFn
from rag.shared.llm import embed as llm_embed


def make_litellm_backend(model: str) -> EmbedFn:
    def embed(texts: list[str]) -> list[list[float]]:
        return llm_embed(texts, model=model)

    return embed
