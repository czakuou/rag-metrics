"""Domain types for the ingestion slice."""

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel


class ChunkStrategy(StrEnum):
    """Supported document chunking strategies."""

    FIXED = "fixed"
    PARENT_CHILD = "parent_child"


class DocumentMetadata(BaseModel):
    """Metadata describing the source of a document."""

    source: Path
    title: str
    word_count: int
    wikilinks: list[str]


class Document(BaseModel):
    """A raw document loaded from the vault."""

    content: str
    metadata: DocumentMetadata


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


class DocumentOutcome(BaseModel):
    """Raw per-document ingestion result, before aggregation into an IngestionResult."""

    chunk_count: int = 0
    embedded_count: int = 0
    failed_source: str | None = None

    @property
    def failed(self) -> bool:
        return self.failed_source is not None


class IngestionResult(BaseModel):
    """Summary of an ingestion run."""

    total_documents: int
    total_chunks: int
    total_embedded: int
    failed_documents: list[str]

    @classmethod
    def from_outcomes(cls, outcomes: list[DocumentOutcome]) -> "IngestionResult":
        return cls(
            total_documents=len(outcomes),
            total_chunks=sum(o.chunk_count for o in outcomes),
            total_embedded=sum(o.embedded_count for o in outcomes),
            failed_documents=[o.failed_source for o in outcomes if o.failed_source is not None],
        )
