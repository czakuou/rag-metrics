"""Domain types for the evals slice."""

from pydantic import BaseModel

# TODO: implement


class GoldenExample(BaseModel):
    """A single question/ground-truth pair from the golden dataset."""

    question: str
    ground_truth: str


class EvalResult(BaseModel):
    """Computed RAGAS metric scores for one eval run."""

    scores: dict[str, float]
    passed: bool
