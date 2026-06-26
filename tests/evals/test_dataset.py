"""Tests for rag.evals.dataset."""

from pathlib import Path

import pytest

from rag.evals.dataset import load_golden_dataset
from rag.evals.types import EvalSample

VALID_LINE = (
    '{"question": "q1", "ground_truth": "gt1", "source_notes": ["a.md"], "query_type": "factual"}'
)


def test_load_golden_dataset_returns_eval_samples_for_valid_jsonl(tmp_path: Path) -> None:
    # Given
    dataset_path = tmp_path / "golden.jsonl"
    dataset_path.write_text("\n".join([VALID_LINE] * 3))

    # When
    samples = load_golden_dataset(dataset_path)

    # Then
    assert len(samples) == 3
    assert all(isinstance(sample, EvalSample) for sample in samples)


def test_load_golden_dataset_skips_blank_lines(tmp_path: Path) -> None:
    # Given
    dataset_path = tmp_path / "golden.jsonl"
    dataset_path.write_text(f"{VALID_LINE}\n\n   \n{VALID_LINE}\n")

    # When
    samples = load_golden_dataset(dataset_path)

    # Then
    assert len(samples) == 2


def test_load_golden_dataset_raises_on_invalid_json(tmp_path: Path) -> None:
    # Given
    dataset_path = tmp_path / "golden.jsonl"
    dataset_path.write_text(f"{VALID_LINE}\nnot valid json\n{VALID_LINE}\n")

    # When / Then
    with pytest.raises(ValueError, match="line 2"):
        load_golden_dataset(dataset_path)
