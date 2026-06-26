"""Reranks retrieved chunks by relevance to the query."""

from rag.ingestion.types import Chunk
from rag.retrieval.types import ScoredChunk

# TODO: implement


def rerank(query: str, chunks: list[Chunk]) -> list[ScoredChunk]:
    raise NotImplementedError
