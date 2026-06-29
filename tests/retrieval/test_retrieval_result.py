from pathlib import Path

from rag.ingestion.types import Chunk, ChunkMetadata, ChunkStrategy
from rag.retrieval.types import GradedChunk, RetrievalResult


def _make_graded_chunk(content: str, score: float, threshold: float) -> GradedChunk:
    return GradedChunk(
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
        relevance_score=score,
        threshold=threshold,
    )


def test_retrieval_result_counts_total_retrieved_and_relevant_chunks() -> None:
    # Given
    chunks = [
        _make_graded_chunk("relevant one", score=0.9, threshold=0.5),
        _make_graded_chunk("relevant two", score=0.6, threshold=0.5),
        _make_graded_chunk("irrelevant", score=0.2, threshold=0.5),
    ]

    # When
    result = RetrievalResult(query="some query", chunks=chunks)

    # Then
    assert result.total_retrieved == 3
    assert result.total_relevant == 2
