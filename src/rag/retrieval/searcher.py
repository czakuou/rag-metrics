"""Searches the vector store for chunks relevant to a query."""

from rag.backends.embedding.protocol import EmbedFn
from rag.backends.vectorstore.protocol import VectorStoreBackend
from rag.ingestion.types import EmbeddedChunk


async def search(
    query: str, backend: VectorStoreBackend, embed_fn: EmbedFn, k: int = 10
) -> list[EmbeddedChunk]:
    vector = embed_fn([query])[0]
    return await backend.search(vector, k)
