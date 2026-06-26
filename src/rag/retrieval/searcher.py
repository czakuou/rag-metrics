"""Searches the vector store for chunks relevant to a query."""

from rag.backends.embedding.protocol import EmbedFn
from rag.backends.vectorstore.protocol import VectorStoreBackend
from rag.ingestion.types import Chunk

# TODO: implement


def search(query: str, backend: VectorStoreBackend, embed_fn: EmbedFn, k: int) -> list[Chunk]:
    raise NotImplementedError
