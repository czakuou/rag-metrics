"""Tests for rag.evals.types value objects."""

from rag.evals.types import EvalReport, EvalSample, MetricScores

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


def test_metric_score_fails_when_score_drops_below_baseline_minus_tolerance() -> None:
    # Given
    per_metric_scores = {
        "faithfulness": [0.86, 0.86],  # above the 0.7 threshold, but a regression
        "answer_relevancy": [0.9, 0.9],
        "context_precision": [0.9, 0.9],
    }
    baselines = {"faithfulness": 0.92, "answer_relevancy": 0.9, "context_precision": 0.9}

    # When
    metric_scores = MetricScores.from_ragas_result(
        per_metric_scores, ALL_THRESHOLDS, baselines, regression_tolerance=0.02
    )

    # Then
    faithfulness = next(s for s in metric_scores.scores if s.name == "faithfulness")
    assert faithfulness.regressed is True
    assert faithfulness.passed is False


def test_metric_score_passes_when_score_drops_within_regression_tolerance() -> None:
    # Given
    per_metric_scores = {
        "faithfulness": [0.905, 0.905],  # 1.5pp below baseline — within 2pp tolerance
        "answer_relevancy": [0.9, 0.9],
        "context_precision": [0.9, 0.9],
    }
    baselines = {"faithfulness": 0.92, "answer_relevancy": 0.9, "context_precision": 0.9}

    # When
    metric_scores = MetricScores.from_ragas_result(
        per_metric_scores, ALL_THRESHOLDS, baselines, regression_tolerance=0.02
    )

    # Then
    faithfulness = next(s for s in metric_scores.scores if s.name == "faithfulness")
    assert faithfulness.regressed is False
    assert faithfulness.passed is True


def test_metric_score_is_not_regressed_when_no_baseline_exists_yet() -> None:
    # Given
    per_metric_scores = {
        "faithfulness": [0.9, 0.9],
        "answer_relevancy": [0.9, 0.9],
        "context_precision": [0.9, 0.9],
    }

    # When — no baselines passed, e.g. first-ever eval run
    metric_scores = MetricScores.from_ragas_result(per_metric_scores, ALL_THRESHOLDS)

    # Then
    faithfulness = next(s for s in metric_scores.scores if s.name == "faithfulness")
    assert faithfulness.regressed is False


def _passing_metric_scores() -> MetricScores:
    per_metric_scores = {
        "faithfulness": [0.9, 0.9],
        "answer_relevancy": [0.9, 0.9],
        "context_precision": [0.9, 0.9],
    }
    return MetricScores.from_ragas_result(per_metric_scores, ALL_THRESHOLDS)


def test_eval_report_passes_when_all_metrics_pass_and_no_pipeline_errors() -> None:
    # Given / When
    report = EvalReport.from_metric_scores(
        _passing_metric_scores(), total_samples=2, pipeline_errors=[], failed_samples=[]
    )

    # Then
    assert report.passed is True


def test_eval_report_fails_when_a_sample_errored_even_if_all_metrics_pass() -> None:
    # Given — metric means look healthy, but one sample never made it into the dataset
    report = EvalReport.from_metric_scores(
        _passing_metric_scores(),
        total_samples=3,
        pipeline_errors=[SAMPLE_A.question],
        failed_samples=[],
    )

    # When / Then — the means only describe the samples that survived
    assert report.passed is False


def test_eval_report_passes_when_individual_samples_fall_below_threshold() -> None:
    # Given — per-sample threshold failures are diagnostic; the gate is on metric means
    report = EvalReport.from_metric_scores(
        _passing_metric_scores(),
        total_samples=2,
        pipeline_errors=[],
        failed_samples=[SAMPLE_B.question],
    )

    # When / Then
    assert report.passed is True
