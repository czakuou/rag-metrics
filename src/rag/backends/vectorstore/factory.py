"""Registry mapping `settings.vectorstore_backend` to a concrete VectorStoreBackend."""

from collections.abc import Callable

from sqlalchemy.ext.asyncio import create_async_engine

from rag.backends.vectorstore.pgvector_backend import PgVectorBackend
from rag.backends.vectorstore.protocol import VectorStoreBackend
from rag.config import Settings

type _Factory = Callable[[Settings], VectorStoreBackend]


def _make_pgvector_backend(settings: Settings) -> VectorStoreBackend:
    # `create_async_engine` only builds the pool lazily on first use — it does
    # not need to run inside an event loop, unlike `asyncpg.create_pool`.
    engine = create_async_engine(str(settings.database_url))
    return PgVectorBackend(engine)


_REGISTRY: dict[str, _Factory] = {
    "pgvector": _make_pgvector_backend,
}


def make_vectorstore_backend(settings: Settings) -> VectorStoreBackend:
    """Build the vector store backend selected by `settings.vectorstore_backend`.

    The caller owns the backend's lifetime and must call `backend.dispose()`
    once, from the same event loop used for queries.
    """
    try:
        factory = _REGISTRY[settings.vectorstore_backend]
    except KeyError:
        raise ValueError(f"Unknown vectorstore backend: {settings.vectorstore_backend}") from None
    return factory(settings)
