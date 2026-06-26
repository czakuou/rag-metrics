"""Vector store backend protocol — stateful contract."""

from typing import Protocol

from rag.ingestion.types import Chunk, EmbeddedChunk


class VectorStoreBackend(Protocol):
    """Contract for all vector store implementations."""

    def upsert(self, chunks: list[EmbeddedChunk]) -> None: ...
    def search(self, vector: list[float], k: int) -> list[Chunk]: ...
    def delete(self, ids: list[str]) -> None: ...
