"""Tests for rag.ingestion.chunker."""

from pathlib import Path

from rag.ingestion.chunker import (
    CHILD_CHUNK_SIZE,
    FIXED_CHUNK_SIZE,
    PARENT_CHUNK_SIZE,
    _tokenizer,
    chunk,
)
from rag.ingestion.types import Document, DocumentMetadata
from rag.shared.types import ChunkStrategy

TOKEN_TOLERANCE = 10


def _document(word_count: int) -> Document:
    content = "word " * word_count
    return Document(
        content=content,
        metadata=DocumentMetadata(
            source=Path("vault/test.md"),
            title="Test",
            word_count=word_count,
            wikilinks=[],
        ),
    )


def test_fixed_chunker_splits_long_document_into_multiple_chunks() -> None:
    # Given
    long_document = _document(word_count=2000)

    # When
    chunks = chunk(long_document, strategy=ChunkStrategy.FIXED)

    # Then
    assert len(chunks) > 1


def test_fixed_chunker_respects_token_limit() -> None:
    # Given
    long_document = _document(word_count=2000)

    # When
    chunks = chunk(long_document, strategy=ChunkStrategy.FIXED)

    # Then
    for c in chunks:
        token_count = len(_tokenizer.encode(c.content).ids)
        assert token_count <= FIXED_CHUNK_SIZE + TOKEN_TOLERANCE


def test_fixed_chunker_is_deterministic() -> None:
    # Given
    document = _document(word_count=1500)

    # When
    first_run = chunk(document, strategy=ChunkStrategy.FIXED)
    second_run = chunk(document, strategy=ChunkStrategy.FIXED)

    # Then
    assert [c.id for c in first_run] == [c.id for c in second_run]


def test_fixed_strategy_chunks_have_no_parent() -> None:
    # Given
    document = _document(word_count=1000)

    # When
    chunks = chunk(document, strategy=ChunkStrategy.FIXED)

    # Then
    assert all(c.parent_id is None for c in chunks)


def test_parent_child_strategy_produces_parents_and_children() -> None:
    # Given
    document = _document(word_count=3000)

    # When
    chunks = chunk(document, strategy=ChunkStrategy.PARENT_CHILD)

    # Then
    parents = [c for c in chunks if c.parent_id is None]
    children = [c for c in chunks if c.parent_id is not None]
    assert len(parents) > 0
    assert len(children) > 0


def test_parent_child_children_reference_an_actual_parent() -> None:
    # Given
    document = _document(word_count=3000)

    # When
    chunks = chunk(document, strategy=ChunkStrategy.PARENT_CHILD)

    # Then
    parent_ids = {c.id for c in chunks if c.parent_id is None}
    children = [c for c in chunks if c.parent_id is not None]
    assert all(c.parent_id in parent_ids for c in children)


def test_parent_child_respects_token_limits() -> None:
    # Given
    document = _document(word_count=3000)

    # When
    chunks = chunk(document, strategy=ChunkStrategy.PARENT_CHILD)

    # Then
    for c in chunks:
        token_count = len(_tokenizer.encode(c.content).ids)
        limit = PARENT_CHUNK_SIZE if c.parent_id is None else CHILD_CHUNK_SIZE
        assert token_count <= limit + TOKEN_TOLERANCE


def test_chunk_returns_empty_list_for_empty_document() -> None:
    # Given
    empty_document = _document(word_count=0)
    empty_document = empty_document.model_copy(update={"content": ""})

    # When
    chunks = chunk(empty_document, strategy=ChunkStrategy.FIXED)

    # Then
    assert chunks == []
