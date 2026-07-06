"""Loads the golden dataset and reads/writes baseline scores for the eval gates."""

import json
from datetime import UTC, datetime
from pathlib import Path

from pydantic import ValidationError

from rag.evals.types import EvalReport, EvalSample


def load_golden_dataset(path: Path) -> list[EvalSample]:
    samples: list[EvalSample] = []
    with path.open(encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                samples.append(EvalSample.model_validate(json.loads(stripped)))
            except (json.JSONDecodeError, ValidationError) as exc:
                raise ValueError(
                    f"Invalid golden dataset entry at line {line_number}: {stripped!r}"
                ) from exc
    return samples


def load_baseline_scores(path: Path) -> dict[str, float]:
    """Returns the last known-good metric scores, or {} if no baseline exists yet."""
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        name: score
        for name, score in payload.items()
        if isinstance(score, (int, float)) and not isinstance(score, bool)
    }


def save_baseline_scores(report: EvalReport, path: Path) -> None:
    """Advances the baseline file — but only when the run passed.

    A run that regressed, or that lost samples to pipeline errors, must not become
    the new known-good reference: that would silently reset the regression check to
    the degraded level and defeat its purpose (see ADR-006, baseline advancement rule).
    """
    if not report.passed:
        return
    payload: dict[str, float | bool | int | str] = {
        metric_score.name: metric_score.score for metric_score in report.scores
    }
    payload["passed"] = report.passed
    payload["total_samples"] = report.total_samples
    payload["timestamp"] = datetime.now(UTC).isoformat()
    path.write_text(json.dumps(payload, indent=2) + "\n")
