"""Eval metric thresholds. This is the only place to change CI gate values."""

from rag.config import settings

THRESHOLDS: dict[str, float] = {
    "faithfulness": settings.eval_faithfulness_threshold,
    "answer_relevancy": settings.eval_answer_relevancy_threshold,
    "context_precision": settings.eval_context_precision_threshold,
}
