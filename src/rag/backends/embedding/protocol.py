"""Embedding backend protocol — stateless callable contract.

Provider selection (OpenAI, BGE, Cohere, local, ...) is handled by the LiteLLM
proxy config (`docker/litellm/config.yaml`), not by choosing a backend here.
"""

from collections.abc import Callable

type EmbedFn = Callable[[list[str]], list[list[float]]]
