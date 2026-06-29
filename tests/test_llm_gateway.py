import pytest

from rag.config import settings
from rag.shared.llm import complete, embed


@pytest.mark.integration
def test_llm_gateway_returns_completion_for_simple_prompt() -> None:
    # Given
    messages = [{"role": "user", "content": "Reply with the single word: pong"}]

    # When
    response = complete(messages, model=settings.llm_chat_model)

    # Then
    assert isinstance(response, str)
    assert len(response) > 0


@pytest.mark.integration
def test_llm_gateway_returns_embeddings_of_correct_dimension() -> None:
    # Given
    texts = ["The quick brown fox jumps over the lazy dog."]

    # When
    vectors = embed(texts, model=settings.llm_embed_model)

    # Then
    assert len(vectors) == 1
    assert len(vectors[0]) == 1536
