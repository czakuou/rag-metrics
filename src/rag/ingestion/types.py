"""Domain types for the ingestion slice."""

from enum import StrEnum

from pydantic import BaseModel

# TODO: implement


class ChunkStrategy(StrEnum):
    """Supported document chunking strategies."""

    FIXED = "fixed"
    PARENT_CHILD = "parent_child"
    SEMANTIC = "semantic"


class DocumentMetadata(BaseModel):
    """Metadata describing the source of a document."""

    source: str


class Document(BaseModel):
    """A raw document loaded from the vault."""

    content: str
    metadata: DocumentMetadata


class ChunkMetadata(BaseModel):
    """Metadata describing the origin of a chunk."""

    source: str


class Chunk(BaseModel):
    """A chunk of a document, ready for embedding."""

    id: str
    content: str
    metadata: ChunkMetadata


class EmbeddedChunk(Chunk):
    """A chunk with its embedding vector attached."""

    embedding: list[float]
