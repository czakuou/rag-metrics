"""CI eval gate for the fully wired pipeline: golden dataset -> agent -> RAGAS.

Unlike test_golden_dataset.py (which evaluates retrieval + a bare LLM synthesis call),
this evaluates the actual ReAct agent end to end, including tool dispatch and the
BAML-driven loop.
Run explicitly with: pytest -m integration tests/evals/test_agent_golden_dataset.py
"""

import asyncio
from pathlib import Path

import pytest

from rag.agent.react import run_react_loop
from rag.agent.types import Observation
from rag.config import settings
from rag.evals.dataset import load_golden_dataset
from rag.evals.runner import run_evals
from rag.evals.thresholds import THRESHOLDS

pytestmark = pytest.mark.integration

GOLDEN_DATASET_PATH = Path("data/golden_dataset.jsonl")


def _agent_pipeline(question: str) -> tuple[str, list[str]]:
    last_observation: Observation | None = None

    def capture_observation(observation: Observation) -> None:
        nonlocal last_observation
        last_observation = observation

    async def run() -> tuple[str, list[str]]:
        result = await run_react_loop(question, settings, on_observation=capture_observation)
        contexts = last_observation.result.split("\n\n") if last_observation else []
        return result.answer, contexts

    return asyncio.run(run())


def test_agent_golden_dataset_meets_all_thresholds() -> None:
    # Given
    samples = load_golden_dataset(GOLDEN_DATASET_PATH)

    # When
    report = run_evals(samples, _agent_pipeline, THRESHOLDS)

    # Then
    assert report.passed, f"Failing questions: {report.failed_samples}"
