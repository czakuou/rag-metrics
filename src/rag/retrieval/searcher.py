"""Searches the vector store for chunks relevant to a query."""

from rag.backends.embedding.protocol import EmbedFn
from rag.backends.vectorstore.protocol import VectorStoreBackend
from rag.shared.types import ScoredChunk


async def search(
    query: str, backend: VectorStoreBackend, embed_fn: EmbedFn, k: int = 10
) -> list[ScoredChunk]:
    vector = embed_fn([query])[0]
    return await backend.search(vector, k)
