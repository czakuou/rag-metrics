"""ReAct reasoning loop: think, act, observe until an answer is reached."""

from collections.abc import Callable

from rag.agent.baml_client import b
from rag.agent.baml_client.types import Action, FinalAnswer, Thought
from rag.agent.tools import RetrievalFn, dispatch_tool
from rag.agent.types import AgentResult, Observation, ToolCall
from rag.config import Settings
from rag.retrieval.pipeline import run_retrieval

type ReActStepFn = Callable[[str, str, str], Thought | Action | FinalAnswer]
type ObservationCallback = Callable[[Observation], None]


async def run_react_loop(
    query: str,
    config: Settings,
    react_step_fn: ReActStepFn = b.ReActStep,
    retrieval_fn: RetrievalFn = run_retrieval,
    on_observation: ObservationCallback | None = None,
) -> AgentResult:
    history: list[str] = []
    tool_calls: list[ToolCall] = []
    context = ""
    iterations = 0

    while iterations < config.agent_max_iterations:
        step = react_step_fn(query, context, "\n".join(history))

        match step:
            case FinalAnswer():
                return AgentResult(
                    answer=step.answer,
                    citations=step.citations,
                    iterations=iterations + 1,
                    tool_calls=tool_calls,
                )
            case Action():
                observation = await dispatch_tool(step, config, retrieval_fn=retrieval_fn)
                if on_observation is not None:
                    on_observation(observation)
                tool_calls.append(ToolCall(tool_name=step.tool_name, tool_input=step.tool_input))
                history.append(f"Action: {step.tool_name}({step.tool_input})")
                history.append(f"Observation: {observation.result}")
                context = observation.result
            case Thought():
                history.append(f"Thought: {step.reasoning}")

        iterations += 1

    return AgentResult(
        answer="Max iterations reached.",
        citations=[],
        iterations=iterations,
        tool_calls=tool_calls,
    )
