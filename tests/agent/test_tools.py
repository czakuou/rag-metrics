from pathlib import Path

from rag.agent.baml_client.types import Action
from rag.agent.tools import dispatch_tool
from rag.ingestion.types import Chunk, ChunkMetadata, ChunkStrategy
from rag.retrieval.types import GradedChunk, RetrievalResult


def _make_graded_chunk(content: str, source: str, score: float, threshold: float) -> GradedChunk:
    return GradedChunk(
        chunk=Chunk(
            id=content,
            content=content,
            metadata=ChunkMetadata(
                source=Path(source),
                title="test",
                chunk_index=0,
                strategy=ChunkStrategy.FIXED,
            ),
        ),
        relevance_score=score,
        threshold=threshold,
    )


async def test_dispatch_tool_returns_observation_with_result_when_retrieval_finds_chunks(
    test_settings,
) -> None:
    # Given
    chunks = [_make_graded_chunk("Paris is the capital of France.", "france.md", 0.9, 0.5)]

    async def fake_retrieval_fn(query: str, config) -> RetrievalResult:
        return RetrievalResult(query=query, chunks=chunks)

    action = Action(tool_name="vector_search", tool_input="capital of France")

    # When
    observation = await dispatch_tool(action, test_settings, retrieval_fn=fake_retrieval_fn)

    # Then
    assert observation.tool_name == "vector_search"
    assert observation.result != ""
    assert observation.source_notes == ["france.md"]


async def test_dispatch_tool_returns_error_observation_for_unknown_tool_without_raising(
    test_settings,
) -> None:
    # Given
    action = Action(tool_name="unknown_tool", tool_input="anything")

    # When
    observation = await dispatch_tool(action, test_settings)

    # Then
    assert observation.tool_name == "unknown_tool"
    assert "Unknown tool" in observation.result
    assert observation.source_notes == []
