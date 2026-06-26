"""Embeds chunks into vectors using the configured embedding backend."""

import structlog

from rag.backends.embedding.protocol import EmbedFn
from rag.ingestion.types import Chunk, EmbeddedChunk

logger = structlog.get_logger()

EMBED_BATCH_SIZE = 100


def embed(chunks: list[Chunk], backend: EmbedFn) -> list[EmbeddedChunk]:
    """Embed chunks, skipping parent chunks that exist for context only."""
    embeddable = [c for c in chunks if c.is_embeddable]

    embedded: list[EmbeddedChunk] = []
    for batch_start in range(0, len(embeddable), EMBED_BATCH_SIZE):
        batch = embeddable[batch_start : batch_start + EMBED_BATCH_SIZE]
        try:
            vectors = backend([c.content for c in batch])
        except Exception:
            logger.error(
                "embedding_batch_failed",
                batch_start=batch_start,
                batch_end=batch_start + len(batch),
            )
            raise
        embedded.extend(
            EmbeddedChunk(chunk=c, embedding=vector)
            for c, vector in zip(batch, vectors, strict=True)
        )
    return embedded
