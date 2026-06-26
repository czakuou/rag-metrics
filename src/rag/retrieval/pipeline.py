"""Main entrypoint for the retrieval slice: query to rerank to grade."""

from rag.backends.embedding.protocol import EmbedFn
from rag.backends.vectorstore.protocol import VectorStoreBackend
from rag.retrieval.types import GradedChunk

# TODO: implement


def run(query: str, backend: VectorStoreBackend, embed_fn: EmbedFn, k: int) -> list[GradedChunk]:
    raise NotImplementedError


if __name__ == "__main__":
    pass
