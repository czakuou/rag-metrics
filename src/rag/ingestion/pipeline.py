"""Main entrypoint for the ingestion slice: vault to chunks to vector store."""

import asyncio
import sys
from pathlib import Path

import structlog

from rag.backends.embedding.litellm_backend import make_litellm_backend
from rag.backends.embedding.protocol import EmbedFn
from rag.backends.vectorstore.factory import make_vectorstore_backend
from rag.backends.vectorstore.protocol import VectorStoreBackend
from rag.config import settings
from rag.ingestion.chunker import chunk
from rag.ingestion.embedder import embed
from rag.ingestion.loader import load_vault
from rag.ingestion.types import Document, DocumentOutcome, IngestionResult
from rag.shared.logging import configure_logging
from rag.shared.types import ChunkStrategy

logger = structlog.get_logger()


async def run(
    backend: VectorStoreBackend, embed_fn: EmbedFn, chunking_strategy: ChunkStrategy
) -> IngestionResult:
    """Ingest every document in the vault into the vector store."""
    documents = load_vault(Path("vault"))
    outcomes = [
        await _ingest_document(doc, chunking_strategy, backend, embed_fn) for doc in documents
    ]
    return IngestionResult.from_outcomes(outcomes)


async def _ingest_document(
    document: Document,
    strategy: ChunkStrategy,
    backend: VectorStoreBackend,
    embed_fn: EmbedFn,
) -> DocumentOutcome:
    try:
        chunks = chunk(document, strategy)
        embedded_chunks = embed(chunks, embed_fn)
        await backend.upsert(embedded_chunks)
    except Exception as exc:
        logger.error("ingestion_failed", source=str(document.metadata.source), error=str(exc))
        return DocumentOutcome(failed_source=str(document.metadata.source))
    return DocumentOutcome(chunk_count=len(chunks), embedded_count=len(embedded_chunks))


async def _run_and_report() -> IngestionResult:
    backend = make_vectorstore_backend(settings)
    embed_fn = make_litellm_backend(model=settings.llm_embed_model)
    try:
        return await run(backend, embed_fn, settings.chunking_strategy)
    finally:
        await backend.dispose()


def main() -> None:
    configure_logging()
    result = asyncio.run(_run_and_report())
    logger.info(
        "ingestion_complete",
        total_documents=result.total_documents,
        total_chunks=result.total_chunks,
        total_embedded=result.total_embedded,
        failed_documents=result.failed_documents,
    )
    print(result.model_dump_json(indent=2))

    sys.exit(1 if result.failed_documents else 0)


if __name__ == "__main__":
    main()
