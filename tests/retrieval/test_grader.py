from pathlib import Path

from rag.ingestion.types import Chunk, ChunkMetadata, ChunkStrategy, EmbeddedChunk
from rag.retrieval.grader import grade


def _make_embedded_chunk(content: str, embedding: list[float]) -> EmbeddedChunk:
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
        embedding=embedding,
    )


def test_grade_marks_chunk_as_relevant_when_similarity_above_threshold() -> None:
    # Given
    similar_chunk = _make_embedded_chunk("similar", embedding=[1.0, 0.0])
    query_embedding = [1.0, 0.0]

    # When
    graded = grade([similar_chunk], query_embedding, threshold=0.5)

    # Then
    assert graded[0].is_relevant
    assert graded[0].relevance_score == 1.0


def test_grade_marks_chunk_as_irrelevant_when_similarity_below_threshold() -> None:
    # Given
    dissimilar_chunk = _make_embedded_chunk("dissimilar", embedding=[0.0, 1.0])
    query_embedding = [1.0, 0.0]

    # When
    graded = grade([dissimilar_chunk], query_embedding, threshold=0.5)

    # Then
    assert not graded[0].is_relevant
    assert graded[0].relevance_score == 0.0


def test_grade_preserves_chunk_order_and_count() -> None:
    # Given
    chunks = [
        _make_embedded_chunk("first", embedding=[1.0, 0.0]),
        _make_embedded_chunk("second", embedding=[0.0, 1.0]),
    ]
    query_embedding = [1.0, 0.0]

    # When
    graded = grade(chunks, query_embedding, threshold=0.5)

    # Then
    assert [g.chunk.content for g in graded] == ["first", "second"]
