"""Composes dataset collection, RAGAS evaluation, and scoring into one eval run."""

from ragas import evaluate
from ragas.dataset_schema import EvaluationResult

from rag.evals.collector import PipelineFn, build_evaluation_dataset
from rag.evals.metrics import RAGAS_METRICS, make_ragas_judge_embeddings, make_ragas_judge_llm
from rag.evals.scoring import score_report
from rag.evals.types import EvalReport, EvalSample


def run_evals(
    samples: list[EvalSample],
    pipeline_fn: PipelineFn,
    thresholds: dict[str, float],
    baselines: dict[str, float] | None = None,
    regression_tolerance: float = 0.0,
) -> EvalReport:
    dataset, row_samples, pipeline_errors = build_evaluation_dataset(samples, pipeline_fn)

    result = evaluate(
        dataset,
        metrics=RAGAS_METRICS,
        llm=make_ragas_judge_llm(),
        embeddings=make_ragas_judge_embeddings(),
    )
    assert isinstance(result, EvaluationResult)  # return_executor=False guarantees this

    return score_report(
        row_samples,
        result,
        thresholds,
        len(samples),
        pipeline_errors,
        baselines,
        regression_tolerance,
    )
