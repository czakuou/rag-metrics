"""Loads the golden dataset used to evaluate the RAG pipeline."""

import json
from pathlib import Path

from pydantic import ValidationError

from rag.evals.types import EvalSample


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
