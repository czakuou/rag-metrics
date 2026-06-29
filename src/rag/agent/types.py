"""Domain types for the agent slice."""

from pydantic import BaseModel


class ToolCall(BaseModel):
    tool_name: str
    tool_input: str


class Observation(BaseModel):
    tool_name: str
    result: str
    source_notes: list[str]


class AgentResult(BaseModel):
    """The final outcome of a ReAct loop run."""

    answer: str
    citations: list[str]
    iterations: int
    tool_calls: list[ToolCall]
