"""pgvector-backed implementation of VectorStoreBackend."""

import asyncpg  # type: ignore[import-untyped]

from rag.ingestion.types import Chunk, EmbeddedChunk

# TODO: implement


class PgVectorBackend:
    """Stateful Postgres + pgvector connection pool backend."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    def upsert(self, chunks: list[EmbeddedChunk]) -> None:
        raise NotImplementedError

    def search(self, vector: list[float], k: int) -> list[Chunk]:
        raise NotImplementedError

    def delete(self, ids: list[str]) -> None:
        raise NotImplementedError
