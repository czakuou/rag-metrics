"""Component-level CI eval gate: golden dataset -> retrieval + bare synthesis -> RAGAS.

This gate isolates the retrieval pipeline (chunking, search, rerank, grade) plus a
single deterministic synthesis call. It is one of two gates — the end-to-end gate over
the actual ReAct agent lives in test_agent_golden_dataset.py, with its own baseline
file. See ADR-006 ("Two eval levels") for why both exist.

Requires OPENAI_API_KEY (and the other env vars consumed by rag.config.Settings) since
RAGAS' faithfulness/answer_relevancy/context_precision metrics call a real LLM judge.
Run explicitly with: pytest -m integration tests/evals/test_golden_dataset.py
"""

import asyncio
from collections.abc import Generator
from pathlib import Path

import pytest

from rag.config import settings
from rag.evals.dataset import load_baseline_scores, load_golden_dataset, save_baseline_scores
from rag.evals.runner import run_evals
from rag.evals.thresholds import THRESHOLDS
from rag.evals.types import EvalReport
from rag.retrieval.pipeline import run_retrieval
from rag.shared.llm import complete

pytestmark = pytest.mark.integration

GOLDEN_DATASET_PATH = Path("data/golden_dataset.jsonl")
BASELINE_SCORES_PATH = Path("data/baseline_scores.json")


def _synthesize_answer(question: str, contexts: list[str]) -> str:
    context_block = "\n\n".join(contexts)
    return complete(
        messages=[
            {
                "role": "user",
                "content": f"Context:\n{context_block}\n\nQuestion: {question}\nAnswer:",
            }
        ],
        model=settings.llm_chat_model,
    )


def _retrieval_pipeline(question: str) -> tuple[str, list[str]]:
    result = asyncio.run(run_retrieval(question, settings))
    contexts = [
        graded_chunk.chunk.content for graded_chunk in result.chunks if graded_chunk.is_relevant
    ]
    return _synthesize_answer(question, contexts), contexts


@pytest.fixture(scope="session")
def golden_dataset_report() -> Generator[EvalReport]:
    samples = load_golden_dataset(GOLDEN_DATASET_PATH)
    baselines = load_baseline_scores(BASELINE_SCORES_PATH)
    report = run_evals(
        samples,
        _retrieval_pipeline,
        THRESHOLDS,
        baselines,
        settings.eval_regression_tolerance,
    )
    save_baseline_scores(report, BASELINE_SCORES_PATH)
    yield report


def test_golden_dataset_every_sample_completes_the_pipeline(
    golden_dataset_report: EvalReport,
) -> None:
    # Given/When: golden_dataset_report ran the full RAGAS suite once for the session

    # Then — a sample that crashes the pipeline is excluded from the metric means, so
    # the means alone can look healthy while part of the dataset silently disappeared.
    assert not golden_dataset_report.pipeline_errors, (
        f"{len(golden_dataset_report.pipeline_errors)} of "
        f"{golden_dataset_report.total_samples} samples raised in the pipeline: "
        f"{golden_dataset_report.pipeline_errors}"
    )


def test_golden_dataset_faithfulness_meets_threshold(golden_dataset_report: EvalReport) -> None:
    # Given/When: golden_dataset_report ran the full RAGAS suite once for the session
    metric_score = next(s for s in golden_dataset_report.scores if s.name == "faithfulness")

    # Then
    assert metric_score.passed, (
        f"faithfulness={metric_score.score:.4f} below threshold={metric_score.threshold:.4f}"
    )


def test_golden_dataset_answer_relevancy_meets_threshold(
    golden_dataset_report: EvalReport,
) -> None:
    # Given/When
    metric_score = next(s for s in golden_dataset_report.scores if s.name == "answer_relevancy")

    # Then
    assert metric_score.passed, (
        f"answer_relevancy={metric_score.score:.4f} below threshold={metric_score.threshold:.4f}"
    )


def test_golden_dataset_context_precision_meets_threshold(
    golden_dataset_report: EvalReport,
) -> None:
    # Given/When
    metric_score = next(s for s in golden_dataset_report.scores if s.name == "context_precision")

    # Then
    assert metric_score.passed, (
        f"context_precision={metric_score.score:.4f} below threshold={metric_score.threshold:.4f}"
    )


def test_golden_dataset_faithfulness_does_not_regress_vs_baseline(
    golden_dataset_report: EvalReport,
) -> None:
    # Given/When
    metric_score = next(s for s in golden_dataset_report.scores if s.name == "faithfulness")

    # Then
    assert not metric_score.regressed, (
        f"faithfulness={metric_score.score:.4f} regressed vs. "
        f"baseline={metric_score.baseline} (tolerance={metric_score.regression_tolerance})"
    )


def test_golden_dataset_answer_relevancy_does_not_regress_vs_baseline(
    golden_dataset_report: EvalReport,
) -> None:
    # Given/When
    metric_score = next(s for s in golden_dataset_report.scores if s.name == "answer_relevancy")

    # Then
    assert not metric_score.regressed, (
        f"answer_relevancy={metric_score.score:.4f} regressed vs. "
        f"baseline={metric_score.baseline} (tolerance={metric_score.regression_tolerance})"
    )


def test_golden_dataset_context_precision_does_not_regress_vs_baseline(
    golden_dataset_report: EvalReport,
) -> None:
    # Given/When
    metric_score = next(s for s in golden_dataset_report.scores if s.name == "context_precision")

    # Then
    assert not metric_score.regressed, (
        f"context_precision={metric_score.score:.4f} regressed vs. "
        f"baseline={metric_score.baseline} (tolerance={metric_score.regression_tolerance})"
    )
