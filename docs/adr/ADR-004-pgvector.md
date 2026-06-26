# ADR-002: pgvector as the vector store

## Status

Accepted

## Context

The ingestion pipeline produces embedding vectors that must be stored and searched
by approximate nearest-neighbour (ANN) queries at retrieval time.

Constraints specific to this project:
- Single-node deployment (no Kubernetes, no managed cloud vector DB)
- The application already requires a relational database for metadata storage
  (chunk source, document ID, timestamps)
- The team (solo developer) should not operate two persistence systems if one can
  do the job
- Swappability is required: the `VectorStoreBackend` Protocol must allow replacing
  pgvector without touching retrieval logic

Secondary constraint: the vector store choice must be defensible in a senior
engineering interview. "We used Pinecone because it was easy to set up" is not
a defensible answer. "We used pgvector because it eliminated a service boundary,
and here is the HNSW index configuration and its trade-offs" is.

## Options considered

### Option A — pgvector (PostgreSQL extension)

Adds vector column type and ANN search operators to PostgreSQL.
Supports two index types: IVFFlat and HNSW (see ADR-003 for chunking; index choice
is addressed here).

**HNSW index** (Hierarchical Navigable Small World):
- Build time: O(n log n), slower to build than IVFFlat
- Query time: sub-millisecond at <1M vectors with `ef_search=64`
- No training step required (IVFFlat needs `lists` parameter tuned to dataset size)
- Memory: higher than IVFFlat — approximately `(d * 4 + 8 * M) bytes` per vector
  where d = dimensions, M = max connections per layer (default 16)
- For `text-embedding-3-small` (1536 dimensions) with M=16:
  approximately 6.5 KB per vector → 6.5 GB per million vectors

**Cost:** zero. PostgreSQL is already in the stack.

**Operational cost:** one fewer service to monitor, back up, and debug.

### Option B — Qdrant

Purpose-built vector database written in Rust.
Excellent performance at scale (>10M vectors).
Supports payload filtering, sparse vectors, named collections.
Runs as a separate Docker service with its own persistence volume.

**Trade-off:** introduces a second persistence system. Metadata (chunk source,
document timestamps) must either be duplicated in Qdrant payloads or kept in
PostgreSQL — creating a split-brain problem on updates.

**When Qdrant wins:** >5M vectors, complex multi-tenant filtering, or when the
team already operates it at scale. None of these apply here.

### Option C — Pinecone (managed)

Fully managed, no infrastructure to operate.
Excellent developer experience for getting started quickly.

**Trade-offs:**
- Vendor lock-in: the query API is proprietary
- Cost: free tier limited to 1 index, 100K vectors — acceptable for a portfolio
  project but not production-representative
- Data leaves the local environment — complicates local development and testing
- Does not demonstrate infrastructure knowledge in an interview

### Option D — ChromaDB

Embedded vector store (runs in-process), good for prototyping.
No separate Docker service required for local development.

**Trade-offs:**
- Not production-grade: ChromaDB's own documentation recommends against it for
  production workloads above a few hundred thousand vectors
- Persistence model is opaque (SQLite under the hood)
- No connection pooling — not suitable for async workloads

## Decision

Chose **Option A — pgvector with HNSW index**.

The decision is driven by the **no second persistence system** principle.
PostgreSQL is already required for metadata. Adding Qdrant would mean operating
two stateful services, two backup strategies, and two failure domains — for a
workload that comfortably fits in pgvector.

HNSW is chosen over IVFFlat because:
1. No training step — IVFFlat requires `VACUUM` and a pre-computed `lists` value
   tuned to the dataset size. HNSW builds incrementally.
2. Better recall at the same latency budget for datasets under 1M vectors.
3. Simpler operational story: no `lists` parameter to retune when the dataset grows.

The `VectorStoreBackend` Protocol in `backends/vectorstore/protocol.py` means
Qdrant can be added later as `qdrant_backend.py` without modifying retrieval logic.
The swap is one line in `.env`.

## Consequences

**Gain:**
- Zero additional infrastructure cost
- Metadata and vectors in the same transaction boundary — no split-brain on updates
- HNSW index gives <5ms p99 query latency for the expected dataset size
  (<100K vectors for an Obsidian vault)
- Defensible in an interview: can explain HNSW graph structure, `ef_search` tuning,
  and the IVFFlat trade-off

**Lose:**
- pgvector does not support sparse vectors (BM25 hybrid search) natively —
  requires `pg_bm25` (ParadeDB) or a separate BM25 index. Hybrid search is
  out of scope for v1.
- ANN performance at >5M vectors is worse than Qdrant — not a concern for this
  dataset size

**Index configuration to use:**

```sql
CREATE INDEX ON chunks
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

`m = 16`: max connections per layer. Higher = better recall, more memory.
`ef_construction = 64`: size of the candidate list during index build.
Higher = better recall, slower build. 64 is the pgvector default and appropriate
for this dataset size.

`ef_search` (set at query time, not index time):
```sql
SET hnsw.ef_search = 40;  -- default 40, increase for higher recall at cost of latency
```

**Technical debt:**
- HNSW index must be rebuilt (`REINDEX`) after bulk inserts > 10% of dataset size
  to maintain recall quality. Add a `make reindex` target when dataset exceeds
  10K vectors.

## Addendum: SQLAlchemy Core async as the database client (not raw asyncpg)

### Context

`PgVectorBackend` was first implemented directly on `asyncpg.Pool`. This surfaced a
real bug, not a style nitpick: `asyncpg.create_pool()` returns a pool bound to the
event loop it was created in. The ingestion pipeline built the pool inside one
`asyncio.run()` call (in the backend factory) and then called `backend.upsert()` /
`.search()` from synchronous wrapper methods that each did their own `asyncio.run()`.
Every call after the first ran in a **new** event loop, while the pool still held
connections registered against the **first, already-closed** loop — a setup that
fails with `RuntimeError` or leaks connections depending on asyncpg version and
timing. Nothing in the codebase ever called `pool.close()` either, so even a
correctly-scoped pool would leak file descriptors over the life of a long-running
process (e.g. the future agent/retrieval slice, which calls `search()` many times
per request).

### Options considered

- **Option A — keep raw `asyncpg`, fix lifecycle by hand.** Thread a single
  event loop through the whole pipeline manually, add an explicit `pool.close()`,
  and make every backend method `async def` so nothing nested calls `asyncio.run()`
  again. Works, but the discipline ("exactly one loop, exactly one pool, dispose
  once") is enforced by convention only — every new call site can reintroduce the
  same bug by reaching for `asyncio.run()` out of habit.
- **Option B — SQLAlchemy Core async (`create_async_engine`, `text()`), no ORM.**
  `AsyncEngine` owns the connection pool. Critically, `create_async_engine()` does
  **not** require an event loop to construct — the pool is opened lazily on first
  use, inside whichever loop is live at query time. This removes the "pool created
  in loop A, used in loop B" failure mode structurally instead of by convention.
  Disposal is one explicit call: `await engine.dispose()`. SQL stays as hand-written
  `text()` statements — no declarative models, no sessions, no relationships. This
  keeps the "no ORM" stance from this ADR's original decision: SQLAlchemy is used
  here purely as a connection-pool manager with a thin execution API, not as an
  object-relational mapper.
- **Option C — SQLAlchemy ORM (declarative models, async sessions).** Rejected for
  the same reason LangChain/LlamaIndex are rejected in ADR-005: it would map
  `Chunk`/`Document` onto ORM model classes with `Mapped[...]` fields and
  `relationship()` for `parent_id`, duplicating the Pydantic domain types in this
  codebase's `ingestion/types.py` and adding session-management concepts (identity
  map, unit of work) that the actual workload — a handful of upsert/search/delete
  queries — does not need.

### Decision

Chose **Option B — SQLAlchemy Core async as the connection layer, raw `text()` SQL,
no ORM models.**

`pgvector` integrates with SQLAlchemy the same way it integrates with asyncpg
(`pgvector.sqlalchemy.Vector` mirrors `pgvector.asyncpg.register_vector`), so this
is not a trade against pgvector itself — only against which Python client drives
the connection. asyncpg remains installed as SQLAlchemy's underlying async driver
(`postgresql+asyncpg://` in `DATABASE_URL`); nothing about the wire protocol changes.

The deciding factor is lifecycle, not ergonomics: `AsyncEngine` makes "one pool,
built once, disposed once, from whichever loop is running" the natural way to use
the API, rather than something the caller must remember to do correctly across
every backend implementation that gets added later (Qdrant, or a second pgvector
backend for tests).

### Consequences

**Gain:**
- The loop-mismatch class of bug is now structurally hard to write — there is no
  `asyncio.run()` left inside `PgVectorBackend` or the vectorstore factory.
- `VectorStoreBackend.dispose()` is now part of the Protocol — every backend
  implementation is required to expose a way to release its resources, and
  `pipeline.py` calls it in a `finally` block around the single `asyncio.run()`
  that drives the whole ingestion run.
- `backends/vectorstore/factory.py::make_vectorstore_backend()` is synchronous —
  building the engine does not need an event loop, simplifying dependency wiring
  in `pipeline.py` (no nested `asyncio.run()` just to construct dependencies).

**Lose:**
- One more dependency (`sqlalchemy[asyncio]`) beyond `asyncpg` + `pgvector`.
- `text()` parameter binding (`:name` placeholders, dict params) reads slightly
  less directly than asyncpg's positional `$1, $2` — a small readability cost for
  the lifecycle guarantee.

**Technical debt:**
- If a second vector store backend is added (e.g. Qdrant per Option B in the main
  decision above), it must implement `dispose()` too, even though e.g. a Qdrant
  HTTP client may not need pool lifecycle management the same way — the Protocol
  method exists for the lowest common denominator (anything stateful must be
  released).
