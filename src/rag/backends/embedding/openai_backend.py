"""OpenAI embedding backend implementation."""

import litellm

from rag.backends.embedding.protocol import EmbedFn


def make_openai_backend(model: str = "text-embedding-3-small") -> EmbedFn:
    def embed(texts: list[str]) -> list[list[float]]:
        response = litellm.embedding(model=model, input=texts)
        return [item["embedding"] for item in response.data]

    return embed
