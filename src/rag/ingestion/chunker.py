"""Splits documents into chunks according to a chunking strategy."""

from collections.abc import Callable

from tokenizers import Tokenizer

from rag.ingestion.types import Chunk, ChunkMetadata, ChunkStrategy, Document

_tokenizer: Tokenizer = Tokenizer.from_pretrained("gpt2")

FIXED_CHUNK_SIZE = 512
FIXED_CHUNK_OVERLAP = 64

PARENT_CHUNK_SIZE = 1024
CHILD_CHUNK_SIZE = 256
CHILD_CHUNK_OVERLAP = 32


def chunk(doc: Document, strategy: ChunkStrategy) -> list[Chunk]:
    """Split a document into chunks using the given strategy."""
    return _STRATEGIES[strategy](doc)


def _token_windows(token_ids: list[int], size: int, step: int) -> list[list[int]]:
    """Slide a window of `size` tokens over `token_ids` with the given `step`."""
    if not token_ids:
        return []
    windows = [token_ids[start : start + size] for start in range(0, len(token_ids), step)]
    return [w for w in windows if w]


def _build_chunk(
    *,
    chunk_id: str,
    token_window: list[int],
    chunk_index: int,
    doc: Document,
    strategy: ChunkStrategy,
    parent_id: str | None,
) -> Chunk | None:
    """Decode a token window into a Chunk, or None if it decodes to blank text."""
    text = _tokenizer.decode(token_window)
    if not text.strip():
        return None
    return Chunk(
        id=chunk_id,
        content=text,
        metadata=ChunkMetadata(
            source=doc.metadata.source,
            title=doc.metadata.title,
            chunk_index=chunk_index,
            strategy=strategy,
        ),
        parent_id=parent_id,
    )


def _fixed_size(doc: Document) -> list[Chunk]:
    token_ids = _tokenizer.encode(doc.content).ids
    source_stem = doc.metadata.source.stem
    step = FIXED_CHUNK_SIZE - FIXED_CHUNK_OVERLAP

    windows = _token_windows(token_ids, FIXED_CHUNK_SIZE, step)
    chunks = (
        _build_chunk(
            chunk_id=f"{source_stem}-{i}",
            token_window=window,
            chunk_index=i,
            doc=doc,
            strategy=ChunkStrategy.FIXED,
            parent_id=None,
        )
        for i, window in enumerate(windows)
    )
    return [c for c in chunks if c is not None]


def _parent_child(doc: Document) -> list[Chunk]:
    token_ids = _tokenizer.encode(doc.content).ids
    source_stem = doc.metadata.source.stem

    parent_windows = _token_windows(token_ids, PARENT_CHUNK_SIZE, PARENT_CHUNK_SIZE)
    parents = [
        _build_chunk(
            chunk_id=f"{source_stem}-parent-{i}",
            token_window=window,
            chunk_index=i,
            doc=doc,
            strategy=ChunkStrategy.PARENT_CHILD,
            parent_id=None,
        )
        for i, window in enumerate(parent_windows)
    ]

    children = [
        child
        for i, (parent, parent_window) in enumerate(zip(parents, parent_windows, strict=True))
        if parent is not None
        for child in _children_of(parent, parent_window, parent_index=i, doc=doc)
    ]

    return [p for p in parents if p is not None] + children


def _children_of(
    parent: Chunk, parent_window: list[int], *, parent_index: int, doc: Document
) -> list[Chunk]:
    source_stem = doc.metadata.source.stem
    step = CHILD_CHUNK_SIZE - CHILD_CHUNK_OVERLAP
    windows = _token_windows(parent_window, CHILD_CHUNK_SIZE, step)
    children = (
        _build_chunk(
            chunk_id=f"{source_stem}-child-{parent_index}-{j}",
            token_window=window,
            chunk_index=j,
            doc=doc,
            strategy=ChunkStrategy.PARENT_CHILD,
            parent_id=parent.id,
        )
        for j, window in enumerate(windows)
    )
    return [c for c in children if c is not None]


_STRATEGIES: dict[ChunkStrategy, Callable[[Document], list[Chunk]]] = {
    ChunkStrategy.FIXED: _fixed_size,
    ChunkStrategy.PARENT_CHILD: _parent_child,
}
