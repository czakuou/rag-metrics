"""Turns a RAGAS evaluation result into a domain EvalReport. Pure — no I/O, no LLM calls."""

from ragas.dataset_schema import EvaluationResult

from rag.evals.metrics import RAGAS_METRICS
from rag.evals.types import EvalReport, EvalSample, MetricScores


def score_report(
    row_samples: list[EvalSample],
    result: EvaluationResult,
    thresholds: dict[str, float],
    total_samples: int,
    pipeline_errors: list[str],
    baselines: dict[str, float] | None = None,
    regression_tolerance: float = 0.0,
) -> EvalReport:
    per_metric_scores = {metric.name: result[metric.name] for metric in RAGAS_METRICS}

    metric_scores = MetricScores.from_ragas_result(
        per_metric_scores, thresholds, baselines, regression_tolerance
    )
    threshold_failures = metric_scores.failing_questions(row_samples, per_metric_scores)

    return EvalReport.from_metric_scores(
        metric_scores, total_samples, pipeline_errors, threshold_failures
    )
