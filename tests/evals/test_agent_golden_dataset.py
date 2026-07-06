"""End-to-end CI eval gate: golden dataset -> ReAct agent -> RAGAS.

Unlike test_golden_dataset.py (the component-level gate over retrieval + a bare
synthesis call), this evaluates the pipeline users actually get: the full ReAct agent,
including tool dispatch and the BAML-driven loop. It gates on the same thresholds but
keeps its own baseline file — agent answers come from a different generation path, so
their score distribution is not comparable to the component gate's baseline.
See ADR-006 ("Two eval levels") for the design rationale.

Requires OPENAI_API_KEY (and the other env vars consumed by rag.config.Settings) since
RAGAS' faithfulness/answer_relevancy/context_precision metrics call a real LLM judge.
Run explicitly with: pytest -m integration tests/evals/test_agent_golden_dataset.py
"""

import asyncio
from collections.abc import Generator
from pathlib import Path

import pytest

from rag.agent.react import run_react_loop
from rag.agent.types import Observation
from rag.config import settings
from rag.evals.dataset import load_baseline_scores, load_golden_dataset, save_baseline_scores
from rag.evals.runner import run_evals
from rag.evals.thresholds import THRESHOLDS
from rag.evals.types import EvalReport

pytestmark = pytest.mark.integration

GOLDEN_DATASET_PATH = Path("data/golden_dataset.jsonl")
AGENT_BASELINE_SCORES_PATH = Path("data/agent_baseline_scores.json")

METRIC_NAMES = ["faithfulness", "answer_relevancy", "context_precision"]


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


@pytest.fixture(scope="session")
def agent_golden_dataset_report() -> Generator[EvalReport]:
    samples = load_golden_dataset(GOLDEN_DATASET_PATH)
    baselines = load_baseline_scores(AGENT_BASELINE_SCORES_PATH)
    report = run_evals(
        samples,
        _agent_pipeline,
        THRESHOLDS,
        baselines,
        settings.eval_regression_tolerance,
    )
    save_baseline_scores(report, AGENT_BASELINE_SCORES_PATH)
    yield report


def test_agent_golden_dataset_every_sample_completes_the_pipeline(
    agent_golden_dataset_report: EvalReport,
) -> None:
    # Given/When: agent_golden_dataset_report ran the full RAGAS suite once for the session

    # Then — a sample that crashes the agent is excluded from the metric means, so
    # the means alone can look healthy while part of the dataset silently disappeared.
    assert not agent_golden_dataset_report.pipeline_errors, (
        f"{len(agent_golden_dataset_report.pipeline_errors)} of "
        f"{agent_golden_dataset_report.total_samples} samples raised in the agent: "
        f"{agent_golden_dataset_report.pipeline_errors}"
    )


@pytest.mark.parametrize("metric_name", METRIC_NAMES)
def test_agent_golden_dataset_metric_meets_threshold(
    agent_golden_dataset_report: EvalReport, metric_name: str
) -> None:
    # Given/When
    metric_score = next(s for s in agent_golden_dataset_report.scores if s.name == metric_name)

    # Then
    assert metric_score.score >= metric_score.threshold, (
        f"{metric_name}={metric_score.score:.4f} below threshold={metric_score.threshold:.4f}"
    )


@pytest.mark.parametrize("metric_name", METRIC_NAMES)
def test_agent_golden_dataset_metric_does_not_regress_vs_baseline(
    agent_golden_dataset_report: EvalReport, metric_name: str
) -> None:
    # Given/When
    metric_score = next(s for s in agent_golden_dataset_report.scores if s.name == metric_name)

    # Then
    assert not metric_score.regressed, (
        f"{metric_name}={metric_score.score:.4f} regressed vs. "
        f"baseline={metric_score.baseline} (tolerance={metric_score.regression_tolerance})"
    )
