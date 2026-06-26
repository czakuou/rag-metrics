"""Domain types for the retrieval slice."""

from pydantic import BaseModel

from rag.ingestion.types import Chunk

# TODO: implement


class ScoredChunk(BaseModel):
    """A chunk paired with its relevance score."""

    chunk: Chunk
    score: float


class GradedChunk(BaseModel):
    """A chunk paired with a relevance verdict."""

    chunk: Chunk
    is_relevant: bool
