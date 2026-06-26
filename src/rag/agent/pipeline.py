"""Main entrypoint for the agent slice: ReAct loop to answer."""

from rag.agent.tools import RetrieveToolFn
from rag.agent.types import AgentAnswer

# TODO: implement


def run(query: str, retrieve: RetrieveToolFn, max_iterations: int) -> AgentAnswer:
    raise NotImplementedError


if __name__ == "__main__":
    pass
