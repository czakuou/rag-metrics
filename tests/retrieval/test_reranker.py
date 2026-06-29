from pathlib import Path

from rag.ingestion.types import Chunk, ChunkMetadata, ChunkStrategy, EmbeddedChunk
from rag.retrieval.reranker import rerank


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


def test_reranker_sorts_chunks_by_relevance_to_query() -> None:
    # Given
    relevant_chunk = _make_embedded_chunk(
        "pgvector is a PostgreSQL extension for vector similarity search"
    )
    irrelevant_chunk = _make_embedded_chunk("bananas are a good source of potassium")
    chunks = [irrelevant_chunk, relevant_chunk]

    # When
    reranked = rerank(chunks, "what is pgvector?")

    # Then
    assert reranked[0] == relevant_chunk
    assert reranked[1] == irrelevant_chunk


def test_reranker_returns_empty_list_for_no_chunks() -> None:
    # Given/When
    reranked = rerank([], "any query")

    # Then
    assert reranked == []
