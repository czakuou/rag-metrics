"""Domain types for the retrieval slice."""

from pydantic import BaseModel

from rag.ingestion.types import Chunk


class GradedChunk(BaseModel):
    """A chunk scored against the query, with a relevance verdict."""

    chunk: Chunk
    relevance_score: float
    threshold: float

    @property
    def is_relevant(self) -> bool:
        return self.relevance_score >= self.threshold


class RetrievalResult(BaseModel):
    """Outcome of running a query through search -> rerank -> grade."""

    query: str
    chunks: list[GradedChunk]

    @property
    def total_retrieved(self) -> int:
        return len(self.chunks)

    @property
    def total_relevant(self) -> int:
        return sum(1 for graded_chunk in self.chunks if graded_chunk.is_relevant)
