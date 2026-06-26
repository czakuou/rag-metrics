"""Tests for rag.ingestion.embedder."""

from pathlib import Path

from rag.ingestion.embedder import embed
from rag.ingestion.types import Chunk, ChunkMetadata, ChunkStrategy

FAKE_EMBED = lambda texts: [[0.1] * 1536 for _ in texts]  # noqa: E731


def _chunk(chunk_id: str, strategy: ChunkStrategy, parent_id: str | None) -> Chunk:
    return Chunk(
        id=chunk_id,
        content="some content",
        metadata=ChunkMetadata(
            source=Path("vault/test.md"),
            title="Test",
            chunk_index=0,
            strategy=strategy,
        ),
        parent_id=parent_id,
    )


def test_parent_child_strategy_excludes_parents_from_embedding() -> None:
    # Given
    parent = _chunk("test-parent-0", ChunkStrategy.PARENT_CHILD, parent_id=None)
    child = _chunk("test-child-0-0", ChunkStrategy.PARENT_CHILD, parent_id="test-parent-0")

    # When
    embedded = embed([parent, child], FAKE_EMBED)

    # Then
    embedded_ids = {e.chunk.id for e in embedded}
    assert "test-parent-0" not in embedded_ids
    assert "test-child-0-0" in embedded_ids


def test_fixed_strategy_embeds_all_chunks() -> None:
    # Given
    chunks = [_chunk(f"test-{i}", ChunkStrategy.FIXED, parent_id=None) for i in range(3)]

    # When
    embedded = embed(chunks, FAKE_EMBED)

    # Then
    assert len(embedded) == 3


def test_embed_returns_empty_list_for_empty_input() -> None:
    # When
    embedded = embed([], FAKE_EMBED)

    # Then
    assert embedded == []
