"""Embeds chunks into vectors using the configured embedding backend."""

from rag.backends.embedding.protocol import EmbedFn
from rag.ingestion.types import Chunk, EmbeddedChunk

# TODO: implement


def embed(chunks: list[Chunk], backend: EmbedFn) -> list[EmbeddedChunk]:
    raise NotImplementedError
