"""Reranks retrieved chunks by relevance to the query using a cross-encoder."""

from sentence_transformers import CrossEncoder

from rag.retrieval.types import RerankFn
from rag.shared.types import ScoredChunk


def make_cross_encoder_reranker(
    model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
) -> RerankFn:
    """Build a reranker backed by a cross-encoder loaded once, on first use.

    The model is bound inside the closure rather than at module import time, so
    importing `rag.retrieval.reranker` (e.g. from unrelated unit tests) never
    triggers a model load — only calling this factory does.
    """
    cross_encoder = CrossEncoder(model_name)

    def rerank(chunks: list[ScoredChunk], query: str) -> list[ScoredChunk]:
        if not chunks:
            return []
        pairs = [(query, scored.chunk.content) for scored in chunks]
        scores = cross_encoder.predict(pairs)
        return [
            scored
            for scored, _ in sorted(zip(chunks, scores, strict=True), key=lambda pair: -pair[1])
        ]

    return rerank
