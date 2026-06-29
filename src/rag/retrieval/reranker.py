"""Reranks retrieved chunks by relevance to the query using a cross-encoder."""

from sentence_transformers import CrossEncoder

from rag.ingestion.types import EmbeddedChunk

_CROSS_ENCODER = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


def rerank(chunks: list[EmbeddedChunk], query: str) -> list[EmbeddedChunk]:
    if not chunks:
        return []
    pairs = [(query, embedded.chunk.content) for embedded in chunks]
    scores = _CROSS_ENCODER.predict(pairs)
    return [
        embedded
        for embedded, _ in sorted(zip(chunks, scores, strict=True), key=lambda pair: -pair[1])
    ]
