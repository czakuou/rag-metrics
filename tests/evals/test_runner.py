"""Tests for rag.evals.runner."""

import pytest

from rag.evals.runner import run_evals
from rag.evals.types import EvalSample

pytestmark = pytest.mark.integration


GROUND_TRUTH = "The CAP theorem describes consistency, availability, and partition tolerance."


def _make_sample(question: str) -> EvalSample:
    return EvalSample(
        question=question,
        ground_truth=GROUND_TRUTH,
        source_notes=["cap-theorem.md"],
        query_type="factual",
    )


def test_run_evals_returns_passed_report_when_all_scores_above_threshold() -> None:
    # Given
    samples = [_make_sample(f"question {i}") for i in range(3)]

    def perfect_pipeline(question: str) -> tuple[str, list[str]]:
        return (GROUND_TRUTH, [GROUND_TRUTH])

    thresholds = {"faithfulness": 0.0, "answer_relevancy": 0.0, "context_precision": 0.0}

    # When
    report = run_evals(samples, perfect_pipeline, thresholds)

    # Then
    assert report.passed is True
    assert all(metric_score.passed for metric_score in report.scores)


def test_run_evals_returns_failed_report_when_score_below_threshold() -> None:
    # Given
    samples = [_make_sample("question")]

    def empty_pipeline(question: str) -> tuple[str, list[str]]:
        return ("", [])

    thresholds = {"faithfulness": 0.99, "answer_relevancy": 0.99, "context_precision": 0.99}

    # When
    report = run_evals(samples, empty_pipeline, thresholds)

    # Then
    assert report.passed is False


def test_run_evals_fails_report_when_pipeline_fn_raises_for_a_sample() -> None:
    # Given
    samples = [_make_sample(f"question {i}") for i in range(3)]
    call_count = 0

    def flaky_pipeline(question: str) -> tuple[str, list[str]]:
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise RuntimeError("pipeline failure")
        return ("answer", ["context"])

    thresholds = {"faithfulness": 0.0, "answer_relevancy": 0.0, "context_precision": 0.0}

    # When
    report = run_evals(samples, flaky_pipeline, thresholds)

    # Then — the surviving samples are still evaluated, but a run that lost a sample
    # to a crash must not pass: its metric means only describe the samples that survived
    assert samples[1].question in report.pipeline_errors
    assert report.passed is False
