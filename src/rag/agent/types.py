"""Domain types for the agent slice."""

from pydantic import BaseModel

from rag.retrieval.types import GradedChunk

# TODO: implement


class AgentStep(BaseModel):
    """A single thought/action/observation step in the ReAct loop."""

    thought: str
    action: str
    observation: str


class AgentAnswer(BaseModel):
    """The final synthesized answer with supporting context."""

    answer: str
    sources: list[GradedChunk]
