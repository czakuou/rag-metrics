"""Registry mapping `settings.embedding_backend` to a concrete EmbedFn factory."""

from rag.backends.embedding.openai_backend import make_openai_backend
from rag.backends.embedding.protocol import EmbeddingBackendFactory, EmbedFn
from rag.config import Settings

_REGISTRY: dict[str, EmbeddingBackendFactory] = {
    "openai": lambda settings: make_openai_backend(settings.embedding_model),
}


def make_embedding_backend(settings: Settings) -> EmbedFn:
    """Build the embedding backend selected by `settings.embedding_backend`."""
    try:
        factory = _REGISTRY[settings.embedding_backend]
    except KeyError:
        raise ValueError(f"Unknown embedding backend: {settings.embedding_backend}") from None
    return factory(settings)
