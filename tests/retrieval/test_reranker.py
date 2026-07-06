from pathlib import Path

from rag.retrieval.reranker import make_cross_encoder_reranker
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


def test_reranker_sorts_chunks_by_relevance_to_query() -> None:
    # Given
    relevant_chunk = _make_scored_chunk(
        "pgvector is a PostgreSQL extension for vector similarity search"
    )
    irrelevant_chunk = _make_scored_chunk("bananas are a good source of potassium")
    chunks = [irrelevant_chunk, relevant_chunk]
    rerank = make_cross_encoder_reranker()

    # When
    reranked = rerank(chunks, "what is pgvector?")

    # Then
    assert reranked[0] == relevant_chunk
    assert reranked[1] == irrelevant_chunk


def test_reranker_returns_empty_list_for_no_chunks() -> None:
    # Given
    rerank = make_cross_encoder_reranker()

    # When
    reranked = rerank([], "any query")

    # Then
    assert reranked == []
