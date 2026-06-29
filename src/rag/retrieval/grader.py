"""Grades chunks by cosine similarity between their embedding and the query embedding."""

import math

from rag.ingestion.types import EmbeddedChunk, EmbeddingVector
from rag.retrieval.types import GradedChunk


def _cosine_similarity(a: EmbeddingVector, b: EmbeddingVector) -> float:
    dot_product = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    return dot_product / (norm_a * norm_b)


def grade(
    chunks: list[EmbeddedChunk], query_embedding: EmbeddingVector, threshold: float
) -> list[GradedChunk]:
    return [
        GradedChunk(
            chunk=embedded.chunk,
            relevance_score=_cosine_similarity(embedded.embedding, query_embedding),
            threshold=threshold,
        )
        for embedded in chunks
    ]
