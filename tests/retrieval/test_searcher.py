from pathlib import Path

from rag.retrieval.searcher import search
from rag.shared.types import Chunk, ChunkMetadata, ChunkStrategy, ScoredChunk


def _make_scored_chunk(content: str) -> ScoredChunk:
    return ScoredChunk(
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
        relevance_score=0.9,
    )


class _FakeBackend:
    def __init__(self, results: list[ScoredChunk]) -> None:
        self._results = results
        self.last_vector: list[float] | None = None
        self.last_k: int | None = None

    async def search(self, vector: list[float], k: int) -> list[ScoredChunk]:
        self.last_vector = vector
        self.last_k = k
        return self._results


async def test_search_embeds_query_and_delegates_to_backend() -> None:
    # Given
    known_chunks = [_make_scored_chunk("about RAG"), _make_scored_chunk("about pgvector")]
    backend = _FakeBackend(known_chunks)

    def embed_fn(texts: list[str]) -> list[list[float]]:
        return [[0.5, 0.5] for _ in texts]

    # When
    result = await search("what is RAG?", backend, embed_fn, k=2)

    # Then
    assert result == known_chunks
    assert backend.last_vector == [0.5, 0.5]
    assert backend.last_k == 2
