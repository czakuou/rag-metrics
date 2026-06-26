"""Vector store backend protocol — stateful contract."""

from collections.abc import Callable
from typing import Protocol

from rag.config import Settings
from rag.ingestion.types import Chunk, EmbeddedChunk


class VectorStoreBackend(Protocol):
    """Contract for all vector store implementations."""

    async def upsert(self, chunks: list[EmbeddedChunk]) -> None: ...
    async def search(self, vector: list[float], k: int) -> list[Chunk]: ...
    async def delete(self, ids: list[str]) -> None: ...
    async def dispose(self) -> None: ...


type VectorStoreBackendFactory = Callable[[Settings], VectorStoreBackend]
