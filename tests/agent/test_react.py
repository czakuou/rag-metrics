import pytest

from rag.agent.baml_client.types import Action, FinalAnswer, Thought
from rag.agent.react import run_react_loop
from rag.agent.types import Observation
from rag.config import Settings


def _settings(max_iterations: int = 5) -> Settings:
    return Settings(
        openai_api_key="sk-test",
        database_url="postgresql+asyncpg://rag:test@localhost:5432/rag_test",
        agent_max_iterations=max_iterations,
    )


async def test_react_loop_returns_agent_result_when_final_answer_on_first_iteration() -> None:
    # Given
    async def fake_react_step(query: str, context: str, history: str) -> FinalAnswer:
        return FinalAnswer(answer="Paris is the capital of France.", citations=["france.md"])

    # When
    result = await run_react_loop(
        "what is the capital of France?", _settings(), react_step_fn=fake_react_step
    )

    # Then
    assert result.answer == "Paris is the capital of France."
    assert result.citations == ["france.md"]
    assert result.iterations == 1
    assert result.tool_calls == []


async def test_react_loop_dispatches_tool_when_action_returned_then_continues(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    calls = {"count": 0}

    async def fake_react_step(
        query: str, context: str, history: str
    ) -> Thought | Action | FinalAnswer:
        calls["count"] += 1
        if calls["count"] == 1:
            return Action(tool_name="vector_search", tool_input="capital of France")
        return FinalAnswer(answer="Paris.", citations=["france.md"])

    async def fake_dispatch_tool(action: Action, config: Settings, **kwargs: object) -> Observation:
        return Observation(
            tool_name=action.tool_name,
            result="france.md: Paris is the capital of France.",
            source_notes=["france.md"],
        )

    monkeypatch.setattr("rag.agent.react.dispatch_tool", fake_dispatch_tool)

    # When
    result = await run_react_loop(
        "what is the capital of France?", _settings(), react_step_fn=fake_react_step
    )

    # Then
    assert result.answer == "Paris."
    assert result.iterations == 2
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].tool_name == "vector_search"


async def test_react_loop_returns_graceful_result_when_max_iterations_reached() -> None:
    # Given
    async def fake_react_step(query: str, context: str, history: str) -> Thought:
        return Thought(reasoning="still thinking", action_needed=False)

    # When
    result = await run_react_loop(
        "an unanswerable query", _settings(max_iterations=3), react_step_fn=fake_react_step
    )

    # Then
    assert result.answer == "Max iterations reached."
    assert result.citations == []
    assert result.iterations == 3


async def test_react_loop_iterations_count_matches_actual_loop_count() -> None:
    # Given
    calls = {"count": 0}

    async def fake_react_step(query: str, context: str, history: str) -> Thought | FinalAnswer:
        calls["count"] += 1
        if calls["count"] < 3:
            return Thought(reasoning="thinking more", action_needed=False)
        return FinalAnswer(answer="done", citations=[])

    # When
    result = await run_react_loop("some query", _settings(), react_step_fn=fake_react_step)

    # Then
    assert result.iterations == calls["count"] == 3
