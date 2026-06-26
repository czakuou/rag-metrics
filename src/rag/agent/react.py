"""ReAct reasoning loop: think, act, observe until an answer is reached."""

from rag.agent.tools import RetrieveToolFn
from rag.agent.types import AgentStep

# TODO: implement


def run_react_loop(query: str, retrieve: RetrieveToolFn, max_iterations: int) -> list[AgentStep]:
    raise NotImplementedError
