"""Chunk-shaped types shared across slices.

A `Chunk` is produced by `ingestion`, stored and searched by `backends/vectorstore`,
and consumed by `retrieval`. None of those is the "owner" of the concept, so the
type lives here instead of being imported cross-slice from whichever slice happened
to define it first — see CLAUDE.md's "no cross-slice imports" rule.
"""

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel


class ChunkStrategy(StrEnum):
    """Supported document chunking strategies."""

    FIXED = "fixed"
    PARENT_CHILD = "parent_child"


class ChunkMetadata(BaseModel):
    """Metadata describing the origin of a chunk."""

    source: Path
    title: str
    chunk_index: int
    strategy: ChunkStrategy


class Chunk(BaseModel):
    """A chunk of a document, ready for embedding."""

    id: str
    content: str
    metadata: ChunkMetadata
    parent_id: str | None = None

    @property
    def is_parent(self) -> bool:
        return self.parent_id is None

    @property
    def is_embeddable(self) -> bool:
        """Parent chunks in parent-child strategy provide context only — never embedded."""
        if self.metadata.strategy == ChunkStrategy.PARENT_CHILD:
            return not self.is_parent
        return True


type EmbeddingVector = list[float]


class EmbeddedChunk(BaseModel):
    """A chunk with its embedding vector attached."""

    chunk: Chunk
    embedding: EmbeddingVector


class ScoredChunk(BaseModel):
    """A chunk with a relevance score, computed by the vector store as part of search
    (cosine similarity between the chunk's embedding and the query vector, via pgvector's
    `<=>` operator) rather than recomputed in Python from a raw embedding vector.
    """

    chunk: Chunk
    relevance_score: float
