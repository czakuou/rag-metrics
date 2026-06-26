"""Eval pipeline entry point — runs full RAGAS suite and exits non-zero if thresholds fail."""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from rag.evals.dataset import load_golden_dataset
from rag.evals.runner import run_evals
from rag.evals.thresholds import THRESHOLDS
from rag.evals.types import EvalReport
from rag.shared.cli import render_table
from rag.shared.logging import configure_logging, logger

GOLDEN_DATASET_PATH = Path("data/golden_dataset.jsonl")
BASELINE_SCORES_PATH = Path("data/baseline_scores.json")


# TODO: replace with real RAG pipeline once ingestion + retrieval are implemented
def _dummy_pipeline(question: str) -> tuple[str, list[str]]:
    return (
        "This is a placeholder answer.",
        ["This is a placeholder context retrieved from the vault."],
    )


def _format_summary(report: EvalReport) -> str:
    headers = ["Metric", "Score", "Threshold", "Status"]
    rows = [
        [
            metric_score.name,
            f"{metric_score.score:.4f}",
            f"{metric_score.threshold:.4f}",
            "PASS" if metric_score.passed else "FAIL",
        ]
        for metric_score in report.scores
    ]
    failed_count = sum(1 for metric_score in report.scores if not metric_score.passed)
    overall = "PASS" if report.passed else "FAIL"
    overall_line = (
        f"Overall: {overall} ({failed_count}/{len(report.scores)} metrics below threshold)"
    )
    return f"{render_table(headers, rows)}\n{overall_line}"


def _write_baseline_scores(report: EvalReport) -> None:
    payload: dict[str, float | bool | int | str] = {
        metric_score.name: metric_score.score for metric_score in report.scores
    }
    payload["passed"] = report.passed
    payload["total_samples"] = report.total_samples
    payload["timestamp"] = datetime.now(UTC).isoformat()
    BASELINE_SCORES_PATH.write_text(json.dumps(payload, indent=2) + "\n")


def main() -> None:
    configure_logging()
    samples = load_golden_dataset(GOLDEN_DATASET_PATH)
    logger.info("loaded golden dataset", total_samples=len(samples))

    report = run_evals(samples, _dummy_pipeline, THRESHOLDS)

    print(_format_summary(report))
    _write_baseline_scores(report)

    sys.exit(0 if report.passed else 1)


if __name__ == "__main__":
    main()
