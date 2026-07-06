"""pgvector-backed implementation of VectorStoreBackend, using SQLAlchemy Core async."""

from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from rag.ingestion.types import Chunk, ChunkMetadata, ChunkStrategy, EmbeddedChunk


class PgVectorBackend:
    """Stateful Postgres + pgvector backend, built on a SQLAlchemy AsyncEngine.

    The engine owns connection pooling and is bound to the event loop it was
    created in — callers must build and dispose it within the same `asyncio.run()`
    as every query, rather than creating a fresh loop per call.
    """

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def upsert(self, chunks: list[EmbeddedChunk]) -> None:
        if not chunks:
            return
        documents = {
            embedded.chunk.metadata.source.stem: embedded.chunk.metadata for embedded in chunks
        }
        async with self._engine.begin() as conn:
            await conn.execute(
                text(
                    """
                    INSERT INTO documents (id, source, title, word_count, wikilinks)
                    VALUES (:id, :source, :title, 0, ARRAY[]::TEXT[])
                    ON CONFLICT (id) DO NOTHING
                    """
                ),
                [
                    {"id": doc_id, "source": str(metadata.source), "title": metadata.title}
                    for doc_id, metadata in documents.items()
                ],
            )

            await conn.execute(
                text(
                    """
                    INSERT INTO chunks
                        (id, document_id, content, chunk_index, strategy, parent_id, embedding)
                    VALUES
                        (:id, :document_id, :content, :chunk_index, :strategy, :parent_id,
                         :embedding)
                    ON CONFLICT (id) DO UPDATE SET
                        content = EXCLUDED.content,
                        chunk_index = EXCLUDED.chunk_index,
                        strategy = EXCLUDED.strategy,
                        parent_id = EXCLUDED.parent_id,
                        embedding = EXCLUDED.embedding
                    """
                ),
                [
                    {
                        "id": embedded.chunk.id,
                        "document_id": embedded.chunk.metadata.source.stem,
                        "content": embedded.chunk.content,
                        "chunk_index": embedded.chunk.metadata.chunk_index,
                        "strategy": embedded.chunk.metadata.strategy.value,
                        "parent_id": embedded.chunk.parent_id,
                        "embedding": str(embedded.embedding),
                    }
                    for embedded in chunks
                ],
            )

    async def search(self, vector: list[float], k: int) -> list[EmbeddedChunk]:
        async with self._engine.connect() as conn:
            await conn.execute(text("SET hnsw.ef_search = 40"))
            rows = (
                await conn.execute(
                    text(
                        """
                        SELECT id, content, document_id, chunk_index, strategy, parent_id, embedding
                        FROM chunks
                        WHERE embedding IS NOT NULL
                        ORDER BY embedding <=> :vector
                        LIMIT :k
                        """
                    ),
                    {"vector": str(vector), "k": k},
                )
            ).mappings()

            results: list[EmbeddedChunk] = []
            for row in rows:
                content = row["content"]
                if row["parent_id"] is not None:
                    parent = (
                        (
                            await conn.execute(
                                text("SELECT content FROM chunks WHERE id = :id"),
                                {"id": row["parent_id"]},
                            )
                        )
                        .mappings()
                        .first()
                    )
                    if parent is not None:
                        content = parent["content"]

                results.append(
                    EmbeddedChunk(
                        chunk=Chunk(
                            id=row["id"],
                            content=content,
                            metadata=ChunkMetadata(
                                source=Path(row["document_id"]),
                                title=row["document_id"],
                                chunk_index=row["chunk_index"],
                                strategy=ChunkStrategy(row["strategy"]),
                            ),
                            parent_id=row["parent_id"],
                        ),
                        embedding=[
                            float(value) for value in row["embedding"].strip("[]").split(",")
                        ],
                    )
                )
            return results

    async def delete(self, ids: list[str]) -> None:
        async with self._engine.begin() as conn:
            await conn.execute(text("DELETE FROM chunks WHERE id = ANY(:ids)"), {"ids": ids})

    async def dispose(self) -> None:
        """Close the underlying connection pool. Call once, in the same event loop as queries."""
        await self._engine.dispose()
