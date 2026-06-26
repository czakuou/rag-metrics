"""Grades chunks as relevant or irrelevant to a query using an LLM."""

from rag.retrieval.types import GradedChunk, ScoredChunk

# TODO: implement


def grade(query: str, chunks: list[ScoredChunk], threshold: float) -> list[GradedChunk]:
    raise NotImplementedError
