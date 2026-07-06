"""Eval domain types."""

from pydantic import BaseModel

from rag.evals.metrics import RAGAS_METRICS


class EvalSample(BaseModel):
    question: str
    ground_truth: str
    source_notes: list[str]
    query_type: str  # "factual" | "synthesis" | "inferential"


class MetricScore(BaseModel):
    """A single RAGAS metric's mean score, gated against its threshold and its baseline.

    `baseline` is the last known-good score for this metric from
    `data/baseline_scores.json`. Gating on the absolute `threshold` alone lets a metric
    regress from e.g. 0.92 to 0.86 without failing CI, even though that drop is a real
    regression — `regressed` catches that case independently of where `threshold` is set.
    """

    name: str
    score: float
    threshold: float
    baseline: float | None = None
    regression_tolerance: float = 0.0

    @property
    def regressed(self) -> bool:
        if self.baseline is None:
            return False
        return self.score < self.baseline - self.regression_tolerance

    @property
    def passed(self) -> bool:
        return self.score >= self.threshold and not self.regressed

    def failing_questions(
        self, samples: list[EvalSample], per_sample_scores: list[float]
    ) -> list[str]:
        return [
            sample.question
            for sample, sample_score in zip(samples, per_sample_scores, strict=True)
            if sample_score < self.threshold
        ]


class MetricScores(BaseModel):
    """All RAGAS metrics for one eval run — the seam that hides the per-metric loop."""

    scores: list[MetricScore]

    @classmethod
    def from_ragas_result(
        cls,
        per_metric_scores: dict[str, list[float]],
        thresholds: dict[str, float],
        baselines: dict[str, float] | None = None,
        regression_tolerance: float = 0.0,
    ) -> "MetricScores":
        baselines = baselines or {}
        scores = [
            MetricScore(
                name=metric.name,
                score=sum(per_sample_scores) / len(per_sample_scores),
                threshold=thresholds[metric.name],
                baseline=baselines.get(metric.name),
                regression_tolerance=regression_tolerance,
            )
            for metric in RAGAS_METRICS
            for per_sample_scores in [per_metric_scores[metric.name]]
        ]
        return cls(scores=scores)

    @property
    def all_passed(self) -> bool:
        return all(metric_score.passed for metric_score in self.scores)

    def failing_questions(
        self, samples: list[EvalSample], per_metric_scores: dict[str, list[float]]
    ) -> list[str]:
        failing: list[str] = []
        for metric_score in self.scores:
            for question in metric_score.failing_questions(
                samples, per_metric_scores[metric_score.name]
            ):
                if question not in failing:
                    failing.append(question)
        return failing


class EvalReport(BaseModel):
    scores: list[MetricScore]
    passed: bool  # True only if ALL metrics passed
    total_samples: int
    failed_samples: list[str]  # questions that contributed to failures

    @classmethod
    def from_metric_scores(
        cls,
        metric_scores: MetricScores,
        total_samples: int,
        failed_samples: list[str],
    ) -> "EvalReport":
        return cls(
            scores=metric_scores.scores,
            passed=metric_scores.all_passed,
            total_samples=total_samples,
            failed_samples=failed_samples,
        )
