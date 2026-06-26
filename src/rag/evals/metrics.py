"""RAGAS metric definitions."""

from ragas.metrics import Metric, answer_relevancy, context_precision, faithfulness

RAGAS_METRICS: list[Metric] = [faithfulness, answer_relevancy, context_precision]
