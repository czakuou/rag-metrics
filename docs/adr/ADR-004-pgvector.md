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
