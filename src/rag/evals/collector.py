"""Runs the RAG pipeline over golden samples to build a RAGAS evaluation dataset."""

from collections.abc import Callable

from ragas import EvaluationDataset

from rag.evals.types import EvalSample
from rag.shared.logging import logger

type PipelineFn = Callable[[str], tuple[str, list[str]]]


def build_evaluation_dataset(
    samples: list[EvalSample],
    pipeline_fn: PipelineFn,
) -> tuple[EvaluationDataset, list[EvalSample], list[str]]:
    """Returns the RAGAS dataset, the samples included in it, and questions that errored.

    Errored questions are excluded from the dataset (RAGAS cannot score a sample with
    no answer), so the caller must surface them as `EvalReport.pipeline_errors` — they
    gate the run, they are not silently dropped.
    """
    rows: list[dict[str, str | list[str]]] = []
    row_samples: list[EvalSample] = []
    pipeline_errors: list[str] = []

    for sample in samples:
        try:
            answer, contexts = pipeline_fn(sample.question)
        except Exception:
            logger.error("pipeline_fn raised for sample", question=sample.question)
            pipeline_errors.append(sample.question)
            continue
        rows.append(
            {
                "user_input": sample.question,
                "response": answer,
                "retrieved_contexts": contexts,
                "reference": sample.ground_truth,
            }
        )
        row_samples.append(sample)

    return EvaluationDataset.from_list(rows), row_samples, pipeline_errors
