"""Runs the agent over the golden dataset and gates results against thresholds."""

from rag.agent.tools import RetrieveToolFn
from rag.evals.types import EvalResult, GoldenExample

# TODO: implement


def run_eval(examples: list[GoldenExample], retrieve: RetrieveToolFn) -> EvalResult:
    raise NotImplementedError


def gate(result: EvalResult) -> bool:
    raise NotImplementedError
