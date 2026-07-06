"""Grades chunks against a relevance threshold.

The relevance score itself (cosine similarity between the chunk and the query) is
computed by the vector store backend as part of `search()` — see
`backends/vectorstore/pgvector_backend.py::search()`, which does it in the SQL query via
pgvector's `<=>` operator rather than recomputing it here from a raw embedding vector.
"""

from rag.retrieval.types import GradedChunk
from rag.shared.types import ScoredChunk


def grade(chunks: list[ScoredChunk], threshold: float) -> list[GradedChunk]:
    return [
        GradedChunk(
            chunk=scored.chunk,
            relevance_score=scored.relevance_score,
            threshold=threshold,
        )
        for scored in chunks
    ]
