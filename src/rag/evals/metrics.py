"""Computes RAGAS metrics for a batch of agent answers."""

from rag.agent.types import AgentAnswer
from rag.evals.types import EvalResult, GoldenExample

# TODO: implement


def compute_metrics(examples: list[GoldenExample], answers: list[AgentAnswer]) -> EvalResult:
    raise NotImplementedError
