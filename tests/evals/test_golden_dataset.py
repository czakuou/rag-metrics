"""CI eval gate — runs the golden dataset through RAGAS and asserts each metric's threshold.

Requires OPENAI_API_KEY (and the other env vars consumed by rag.config.Settings) since
RAGAS' faithfulness/answer_relevancy/context_precision metrics call a real LLM judge.
Run explicitly with: pytest -m integration tests/evals/test_golden_dataset.py
"""

import asyncio
import json
from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path

import litellm
import pytest

from rag.config import settings
from rag.evals.runner import run_evals
from rag.evals.thresholds import THRESHOLDS
from rag.evals.types import EvalReport
from rag.retrieval.pipeline import run_retrieval

pytestmark = pytest.mark.integration

GOLDEN_DATASET_PATH = Path("data/golden_dataset.jsonl")
BASELINE_SCORES_PATH = Path("data/baseline_scores.json")


def _synthesize_answer(question: str, contexts: list[str]) -> str:
    context_block = "\n\n".join(contexts)
    response = litellm.completion(
        model=settings.llm_model,
        messages=[
            {
                "role": "user",
                "content": f"Context:\n{context_block}\n\nQuestion: {question}\nAnswer:",
            }
        ],
    )
    return str(response.choices[0].message.content)


def _retrieval_pipeline(question: str) -> tuple[str, list[str]]:
    result = asyncio.run(run_retrieval(question, settings))
    contexts = [
        graded_chunk.chunk.content for graded_chunk in result.chunks if graded_chunk.is_relevant
    ]
    return _synthesize_answer(question, contexts), contexts


def _write_baseline_scores(report: EvalReport) -> None:
    payload: dict[str, float | bool | int | str] = {
        metric_score.name: metric_score.score for metric_score in report.scores
    }
    payload["passed"] = report.passed
    payload["total_samples"] = report.total_samples
    payload["timestamp"] = datetime.now(UTC).isoformat()
    BASELINE_SCORES_PATH.write_text(json.dumps(payload, indent=2) + "\n")


@pytest.fixture(scope="session")
def golden_dataset_report() -> Generator[EvalReport]:
    from rag.evals.dataset import load_golden_dataset

    samples = load_golden_dataset(GOLDEN_DATASET_PATH)
    report = run_evals(samples, _retrieval_pipeline, THRESHOLDS)
    _write_baseline_scores(report)
    yield report


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
