"""Splits documents into chunks according to a chunking strategy."""

from rag.ingestion.types import Chunk, ChunkStrategy, Document

# TODO: implement


def chunk(doc: Document, strategy: ChunkStrategy) -> list[Chunk]:
    raise NotImplementedError
