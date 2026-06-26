"""Tests for rag.evals.types value objects."""

from rag.evals.types import EvalSample, MetricScores

SAMPLE_A = EvalSample(
    question="q1", ground_truth="gt1", source_notes=["a.md"], query_type="factual"
)
SAMPLE_B = EvalSample(
    question="q2", ground_truth="gt2", source_notes=["b.md"], query_type="factual"
)


ALL_THRESHOLDS = {"faithfulness": 0.7, "answer_relevancy": 0.7, "context_precision": 0.7}


def test_metric_score_passes_when_score_meets_threshold() -> None:
    # Given
    per_metric_scores = {
        "faithfulness": [0.8, 0.9],
        "answer_relevancy": [0.9, 0.9],
        "context_precision": [0.9, 0.9],
    }

    # When
    metric_scores = MetricScores.from_ragas_result(per_metric_scores, ALL_THRESHOLDS)

    # Then
    faithfulness = next(s for s in metric_scores.scores if s.name == "faithfulness")
    assert faithfulness.passed is True


def test_metric_score_fails_when_mean_score_below_threshold() -> None:
    # Given
    per_metric_scores = {
        "faithfulness": [0.1, 0.2],
        "answer_relevancy": [0.9, 0.9],
        "context_precision": [0.9, 0.9],
    }

    # When
    metric_scores = MetricScores.from_ragas_result(per_metric_scores, ALL_THRESHOLDS)

    # Then
    faithfulness = next(s for s in metric_scores.scores if s.name == "faithfulness")
    assert faithfulness.passed is False


def test_metric_scores_all_passed_is_false_when_any_metric_fails() -> None:
    # Given
    per_metric_scores = {
        "faithfulness": [0.9],
        "answer_relevancy": [0.1],
        "context_precision": [0.9],
    }

    # When
    metric_scores = MetricScores.from_ragas_result(per_metric_scores, ALL_THRESHOLDS)

    # Then
    assert metric_scores.all_passed is False


def test_metric_scores_failing_questions_includes_only_samples_below_threshold() -> None:
    # Given
    samples = [SAMPLE_A, SAMPLE_B]
    per_metric_scores = {
        "faithfulness": [0.9, 0.2],
        "answer_relevancy": [0.9, 0.9],
        "context_precision": [0.9, 0.9],
    }
    metric_scores = MetricScores.from_ragas_result(per_metric_scores, ALL_THRESHOLDS)

    # When
    failing = metric_scores.failing_questions(samples, per_metric_scores)

    # Then
    assert failing == [SAMPLE_B.question]
