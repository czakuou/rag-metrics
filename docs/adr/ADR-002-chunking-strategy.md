# ADR-003: Chunking strategy

## Status

Accepted

## Context

Chunking is the step where a document is split into pieces that are individually
embedded and stored in the vector store. The chunking strategy directly determines
retrieval quality — it is arguably the highest-leverage parameter in the entire RAG
pipeline.

Two failure modes to design against:

**Under-chunking** (chunks too large):
- The embedding of a 2000-token chunk averages over too many concepts
- Cosine similarity to a query is diluted — recall drops
- The retrieved chunk contains the answer but also a lot of noise — faithfulness drops

**Over-chunking** (chunks too small):
- Each chunk lacks enough context to be useful on its own
- The answer may be split across two adjacent chunks — neither scores well in retrieval
- More chunks = more vectors = higher storage and query cost

The Obsidian vault has specific structural properties that inform the decision:
- Notes are written in Markdown with `##` and `###` headers as semantic boundaries
- Notes contain `[[wikilinks]]` that create a graph of related concepts
- Note length varies: some are 100-word definitions, others are 2000-word deep-dives
- A query like "what is attention?" should retrieve the relevant section of a note,
  not the entire note

This ADR evaluates three strategies and selects one as the default, with a second
strategy available via `ChunkStrategy` enum for experimentation.

## Options considered

### Option A — Fixed-size chunking

Split document into chunks of N tokens with an overlap of M tokens.
Overlap prevents answers that span a chunk boundary from being missed entirely.

```
Document: [-------- 2000 tokens --------]
Chunk 1:  [=== 512 ===]
Chunk 2:       [=== 512 ===]          (64-token overlap with chunk 1)
Chunk 3:              [=== 512 ===]
...
```

**Parameters chosen:**
- `chunk_size = 512 tokens` — fits in the context window of all embedding models,
  large enough to contain a full argument
- `chunk_overlap = 64 tokens` — ~12.5% overlap, enough to catch boundary splits
  without excessive redundancy

**Pros:**
- Deterministic and fast — no LLM call required
- Easy to reason about: every chunk is the same size
- Works on any document format

**Cons:**
- Ignores document structure — a 512-token chunk may start mid-sentence or split
  a code block
- For Obsidian notes with clear `##` section boundaries, this is wasteful

### Option B — Parent-child (hierarchical) chunking

Two levels of chunking:
- **Parent chunks** (1024 tokens) — stored for context, not embedded
- **Child chunks** (256 tokens) — embedded and indexed in the vector store

At retrieval time: search by child chunk embedding → return parent chunk as context.

```
Note: [Parent: 1024 tokens]
       ├── Child 1 (256 tokens) → embedded → indexed
       ├── Child 2 (256 tokens) → embedded → indexed
       ├── Child 3 (256 tokens) → embedded → indexed
       └── Child 4 (256 tokens) → embedded → indexed
```

**Pros:**
- Child embedding is more specific → better retrieval precision
- Parent context is richer → better faithfulness (LLM gets more context to answer from)
- Directly addresses the under-chunking / over-chunking trade-off

**Cons:**
- More complex to implement: requires storing parent-child relationships in the DB
- More vectors stored (4x the child chunks of a fixed-size approach for same coverage)
- Requires schema change: `chunks` table needs `parent_id` column

### Option C — Semantic chunking

Use an embedding model to detect semantic boundaries: split when cosine similarity
between adjacent sentences drops below a threshold.

```
Paragraph 1: "Attention is a mechanism..." → high similarity to next sentence
Paragraph 2: "HNSW is an index structure..." → low similarity to paragraph 1 → SPLIT HERE
```

**Pros:**
- Chunks respect conceptual boundaries, not arbitrary token counts
- Best recall for notes with multiple unrelated topics

**Cons:**
- Requires an embedding model call during ingestion (additional cost and latency)
- Non-deterministic: threshold tuning affects chunk count and boundaries
- Harder to reason about: chunk sizes vary, making golden dataset construction harder
- Premature optimisation for v1 — the Obsidian vault already has `##` boundaries
  that encode semantic structure

### Option D — Markdown-aware chunking (header-based)

Split on `##` and `###` headers. Each section becomes one chunk.

**Pros:**
- Perfectly aligned with Obsidian's authoring conventions
- No token counting required; boundaries are explicit in the source

**Cons:**
- Chunk size is entirely author-controlled: one section might be 50 tokens,
  another 3000 tokens
- Long sections exceed embedding model context windows without a secondary split
- Requires fallback to fixed-size for oversized sections — making it a hybrid anyway

## Decision

**Default strategy: Option A — fixed-size chunking (512 tokens, 64 overlap)**
**Available for experimentation: Option B — parent-child chunking**

### Why fixed-size as default

Fixed-size chunking is the correct starting point because:

1. **The golden dataset is built against it.** Changing chunk boundaries changes
   which context is retrieved, which changes eval scores. The baseline in
   `data/baseline_scores.json` is only meaningful if chunking is stable.

2. **It is fast and cheap.** No LLM calls during ingestion. The Obsidian vault
   is small (<100K tokens); ingestion should complete in seconds.

3. **It is the control condition.** To justify adding the complexity of parent-child
   chunking, there must be evidence that it improves RAGAS scores. Fixed-size
   provides that baseline.

### Why parent-child is available (not discarded)

Parent-child chunking addresses a real failure mode: a 512-token chunk may contain
the answer but the LLM does not have enough surrounding context to answer faithfully.
The `ChunkStrategy.PARENT_CHILD` enum value is implemented so that swapping strategy
is one argument change in `pipeline.py`, and the RAGAS gate measures whether the
swap helped or hurt.

### Why semantic chunking is deferred

Semantic chunking requires an embedding call per sentence during ingestion — making
ingestion cost proportional to the LLM pricing, not just compute. For a portfolio
project where ingestion is run repeatedly during development, this is wasteful.
It can be added as `ChunkStrategy.SEMANTIC` if fixed-size + parent-child do not
reach the target RAGAS thresholds.

### Why markdown-aware chunking is not implemented

The fallback-to-fixed-size requirement makes it a strict superset of fixed-size
chunking with added complexity and no guaranteed improvement. Deferred to v2 if
the vault structure makes it clearly beneficial.

## Consequences

**Gain:**
- Ingestion is fast and free (no LLM calls)
- Chunking strategy is swappable via `ChunkStrategy` enum — RAGAS measures
  the impact of any change
- Fixed-size baseline gives a stable foundation for the golden dataset

**Lose:**
- Fixed-size chunks may split mid-argument for long Obsidian sections
- No semantic boundary awareness in v1

**Parameters to monitor:**
- If `context_precision` RAGAS score is below 0.65 on the golden dataset,
  switch to `ChunkStrategy.PARENT_CHILD` and re-run evals.
- If parent-child does not improve `context_precision`, investigate semantic chunking.

**Implementation note:**

The `ChunkStrategy` enum lives in `ingestion/types.py`.
The `chunk()` function in `ingestion/chunker.py` dispatches on it.
The active strategy is set in `config.py` as `chunking_strategy: str = "fixed"`.
No code outside `ingestion/` needs to change when the strategy changes.