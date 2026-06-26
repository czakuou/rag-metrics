"""Embedding backend protocol — stateless callable contract."""

from collections.abc import Callable

type EmbedFn = Callable[[list[str]], list[list[float]]]
