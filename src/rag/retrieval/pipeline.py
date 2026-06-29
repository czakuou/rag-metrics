"""Main entrypoint for the retrieval slice: query -> search -> rerank -> grade."""

import asyncio

from rag.backends.embedding.litellm_backend import make_litellm_backend
from rag.backends.vectorstore.factory import make_vectorstore_backend
from rag.config import Settings, settings
from rag.retrieval.grader import grade
from rag.retrieval.reranker import rerank
from rag.retrieval.searcher import search
from rag.retrieval.types import RetrievalResult


async def run_retrieval(query: str, config: Settings) -> RetrievalResult:
    backend = make_vectorstore_backend(config)
    embed_fn = make_litellm_backend(
        model=config.llm_embed_model,
        base_url=config.litellm_base_url,
        api_key=config.litellm_master_key,
    )
    try:
        retrieved = await search(query, backend, embed_fn, k=config.retrieval_k)
        reranked = rerank(retrieved, query)
        query_embedding = embed_fn([query])[0]
        graded = grade(reranked, query_embedding, config.retrieval_relevance_threshold)
        return RetrievalResult(query=query, chunks=graded)
    finally:
        await backend.dispose()


if __name__ == "__main__":
    result = asyncio.run(run_retrieval("example query", settings))
    print(result.model_dump_json(indent=2))
