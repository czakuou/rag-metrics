"""Tools available to the ReAct agent."""

from collections.abc import Awaitable, Callable

from rag.agent.baml_client.types import Action
from rag.agent.types import Observation
from rag.config import Settings
from rag.retrieval.pipeline import run_retrieval
from rag.retrieval.types import RetrievalResult

type RetrievalFn = Callable[[str, Settings], Awaitable[RetrievalResult]]


def _format_observation(result: RetrievalResult) -> Observation:
    relevant = [graded_chunk for graded_chunk in result.chunks if graded_chunk.is_relevant]
    context = "\n\n".join(
        f"{graded_chunk.chunk.metadata.source.name}: {graded_chunk.chunk.content}"
        for graded_chunk in relevant
    )
    source_notes = [graded_chunk.chunk.metadata.source.name for graded_chunk in relevant]
    return Observation(tool_name="vector_search", result=context, source_notes=source_notes)


async def dispatch_tool(
    action: Action,
    config: Settings,
    retrieval_fn: RetrievalFn = run_retrieval,
) -> Observation:
    if action.tool_name != "vector_search":
        return Observation(
            tool_name=action.tool_name,
            result=f"Unknown tool: {action.tool_name}",
            source_notes=[],
        )
    result = await retrieval_fn(action.tool_input, config)
    return _format_observation(result)
