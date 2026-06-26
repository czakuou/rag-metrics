"""Tools available to the ReAct agent."""

from collections.abc import Callable

from rag.retrieval.types import GradedChunk

# TODO: implement

type RetrieveToolFn = Callable[[str], list[GradedChunk]]
