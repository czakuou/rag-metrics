"""OpenAI embedding backend implementation."""

from rag.backends.embedding.protocol import EmbedFn

# TODO: implement


def make_openai_backend(model: str = "text-embedding-3-small") -> EmbedFn:
    def embed(texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

    return embed
