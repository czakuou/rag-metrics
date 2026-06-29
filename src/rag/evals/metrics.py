"""RAGAS metric definitions and judge LLM — routed through the LiteLLM proxy."""

from langchain_openai import ChatOpenAI
from ragas.embeddings import BaseRagasEmbedding, LiteLLMEmbeddings
from ragas.llms import BaseRagasLLM, LangchainLLMWrapper
from ragas.metrics import Metric, answer_relevancy, context_precision, faithfulness

from rag.config import settings

RAGAS_METRICS: list[Metric] = [faithfulness, answer_relevancy, context_precision]


def make_ragas_judge_llm() -> BaseRagasLLM:
    # ragas.evaluate(llm=...) only accepts BaseRagasLLM/LangChain objects, and this version
    # of ragas has no ragas.llms.LiteLLM wrapper, so ChatOpenAI is used purely as an
    # OpenAI-schema-compatible HTTP client — base_url points at the LiteLLM proxy, not at
    # OpenAI, so the provider stays swappable via litellm config.
    chat = ChatOpenAI(
        model=settings.llm_eval_model,
        api_key=settings.litellm_master_key,
        base_url=settings.litellm_base_url,
    )
    return LangchainLLMWrapper(chat)  # type: ignore[no-any-return]  # ragas stub returns Any


def make_ragas_judge_embeddings() -> BaseRagasEmbedding:
    return LiteLLMEmbeddings(
        model=settings.llm_embed_model,
        api_key=settings.litellm_master_key,
        api_base=settings.litellm_base_url,
    )
