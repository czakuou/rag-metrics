"""Domain types for the ingestion slice.

`Chunk`, `ChunkMetadata`, `ChunkStrategy`, `EmbeddedChunk`, and `EmbeddingVector` live in
`rag.shared.types` instead of here — they are produced by this slice but consumed by
`retrieval` and `backends/vectorstore` too, so they are a cross-slice contract, not an
ingestion-only concept. Import them from `rag.shared.types` directly.
"""

from pathlib import Path

from pydantic import BaseModel


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
