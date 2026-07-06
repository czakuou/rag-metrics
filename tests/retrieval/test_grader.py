from pathlib import Path

from rag.retrieval.grader import grade
from rag.shared.types import Chunk, ChunkMetadata, ChunkStrategy, ScoredChunk


def _make_scored_chunk(content: str, relevance_score: float) -> ScoredChunk:
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
        relevance_score=relevance_score,
    )


def test_grade_marks_chunk_as_relevant_when_similarity_above_threshold() -> None:
    # Given
    similar_chunk = _make_scored_chunk("similar", relevance_score=1.0)

    # When
    graded = grade([similar_chunk], threshold=0.5)

    # Then
    assert graded[0].is_relevant
    assert graded[0].relevance_score == 1.0


def test_grade_marks_chunk_as_irrelevant_when_similarity_below_threshold() -> None:
    # Given
    dissimilar_chunk = _make_scored_chunk("dissimilar", relevance_score=0.0)

    # When
    graded = grade([dissimilar_chunk], threshold=0.5)

    # Then
    assert not graded[0].is_relevant
    assert graded[0].relevance_score == 0.0


def test_grade_preserves_chunk_order_and_count() -> None:
    # Given
    chunks = [
        _make_scored_chunk("first", relevance_score=1.0),
        _make_scored_chunk("second", relevance_score=0.0),
    ]

    # When
    graded = grade(chunks, threshold=0.5)

    # Then
    assert [g.chunk.content for g in graded] == ["first", "second"]
