"""Turns a RAGAS evaluation result into a domain EvalReport. Pure — no I/O, no LLM calls."""

from ragas.dataset_schema import EvaluationResult

from rag.evals.metrics import RAGAS_METRICS
from rag.evals.types import EvalReport, EvalSample, MetricScores


def score_report(
    row_samples: list[EvalSample],
    result: EvaluationResult,
    thresholds: dict[str, float],
    total_samples: int,
    failed_samples: list[str],
) -> EvalReport:
    per_metric_scores = {metric.name: result[metric.name] for metric in RAGAS_METRICS}

    metric_scores = MetricScores.from_ragas_result(per_metric_scores, thresholds)
    threshold_failures = metric_scores.failing_questions(row_samples, per_metric_scores)

    all_failed = list(failed_samples)
    all_failed.extend(question for question in threshold_failures if question not in all_failed)

    return EvalReport.from_metric_scores(metric_scores, total_samples, all_failed)
