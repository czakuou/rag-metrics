from pathlib import Path

from rag.ingestion.types import Chunk, ChunkMetadata, ChunkStrategy, EmbeddedChunk
from rag.retrieval.searcher import search


def _make_embedded_chunk(content: str) -> EmbeddedChunk:
    return EmbeddedChunk(
        chunk=Chunk(
            id=content,
            content=content,
            metadata=ChunkMetadata(
                source=Path("vault/test.md"),
                title="test",
                chunk_index=0,
                strategy=ChunkStrategy.FIXED,
            ),
        ),
        embedding=[1.0, 0.0],
    )


class _FakeBackend:
    def __init__(self, results: list[EmbeddedChunk]) -> None:
        self._results = results
        self.last_vector: list[float] | None = None
        self.last_k: int | None = None

    async def search(self, vector: list[float], k: int) -> list[EmbeddedChunk]:
        self.last_vector = vector
        self.last_k = k
        return self._results


async def test_search_embeds_query_and_delegates_to_backend() -> None:
    # Given
    known_chunks = [_make_embedded_chunk("about RAG"), _make_embedded_chunk("about pgvector")]
    backend = _FakeBackend(known_chunks)

    def embed_fn(texts: list[str]) -> list[list[float]]:
        return [[0.5, 0.5] for _ in texts]

    # When
    result = await search("what is RAG?", backend, embed_fn, k=2)

    # Then
    assert result == known_chunks
    assert backend.last_vector == [0.5, 0.5]
    assert backend.last_k == 2
