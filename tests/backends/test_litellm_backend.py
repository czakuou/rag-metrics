import pytest

from rag.backends.embedding.litellm_backend import make_litellm_backend
from rag.config import settings


@pytest.mark.integration
def test_litellm_backend_returns_vectors_of_correct_dimension() -> None:
    # Given
    embed_fn = make_litellm_backend(
        model=settings.llm_embed_model,
        base_url=settings.litellm_base_url,
        api_key=settings.litellm_master_key,
    )

    # When
    vectors = embed_fn(["The quick brown fox jumps over the lazy dog."])

    # Then
    assert len(vectors) == 1
    assert len(vectors[0]) == 1536
