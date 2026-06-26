"""Embedding backend protocol — stateless callable contract."""

from collections.abc import Callable

from rag.config import Settings

type EmbedFn = Callable[[list[str]], list[list[float]]]
type EmbeddingBackendFactory = Callable[[Settings], EmbedFn]
