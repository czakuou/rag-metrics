# ADR-005: Chunk-shaped types live in `shared/types.py`, not `ingestion/types.py`

## Status

Accepted

## Context

`CLAUDE.md` states a hard rule: "No cross-slice imports except from `backends/` and
`shared/` — a slice reads in isolation." In practice, `retrieval/grader.py`,
`retrieval/reranker.py`, `retrieval/searcher.py`, `retrieval/types.py`, and
`backends/vectorstore/{protocol,pgvector_backend}.py` all imported `Chunk`,
`ChunkMetadata`, `ChunkStrategy`, `EmbeddedChunk`, and `EmbeddingVector` directly
from `rag.ingestion.types` — a straightforward violation of that rule, not a
borderline case.

This was not a typo-level mistake. `ingestion` is genuinely where these types are
*produced* (a document becomes `Chunk`s, a `Chunk` becomes an `EmbeddedChunk`), so
defining them in `ingestion/types.py` and importing them from there reads as natural
while writing the code. But "produced by X" is not the same claim as "owned by X" —
`retrieval` and `backends/vectorstore` depend on these types as data contracts they
must conform to, not as `ingestion`-internal implementation details they happen to
reach into.

## Options considered

### Option A — leave it, treat the rule as aspirational

Cross-slice type imports already work, mypy passes, tests pass. Leaving them as-is
costs nothing functionally.

**Rejected:** the rule in `CLAUDE.md` is written as absolute ("no cross-slice
imports"), and the codebase violates it in five files. A rule the codebase
routinely violates is worse than no rule — it signals the documentation is
aspirational rather than descriptive, which undermines every other rule in the
same file.

### Option B — `agent → retrieval` and `retrieval → ingestion` are both "fine", loosen the rule to allow any cross-slice import

**Rejected:** this erases a real distinction. `agent/react.py` importing
`retrieval.pipeline.run_retrieval` is calling into another slice's *behavior* —
the agent's job is to orchestrate retrieval as one step of the ReAct loop, so this
dependency is the point of having an agent slice at all. `retrieval` importing
`Chunk` from `ingestion.types` is different in kind: `retrieval` does not call
anything in `ingestion`, it just needs the same data shape `ingestion` happens to
have defined first. Treating both as the same category of "cross-slice import" and
blanket-allowing them would also legalize `retrieval` reaching into
`ingestion.chunker._fixed_size()`, which is exactly the coupling the original rule
was trying to prevent.

### Option C — move chunk-shaped types to `rag.shared.types`

`Chunk`, `ChunkMetadata`, `ChunkStrategy`, `EmbeddedChunk`, `EmbeddingVector` move
to a new `shared/types.py`. `ingestion/types.py` keeps only what is genuinely
ingestion-only: `Document`, `DocumentMetadata`, `DocumentOutcome`,
`IngestionResult`. Every former `from rag.ingestion.types import Chunk` becomes
`from rag.shared.types import Chunk`, including within `ingestion/` itself.

**Chosen.**

## Decision

Chose **Option C**, and refined the cross-slice-import rule in `CLAUDE.md` instead
of just enforcing the old wording harder:

- **Importing a type across slices is not allowed.** If two slices need the same
  type, the type moves to `shared/types.py`. This is what actually happened here.
- **Importing a pipeline/orchestration function across slices is allowed**, for a
  slice that is explicitly downstream of another in the data flow (`agent` depends
  on `retrieval`, never the reverse). This was already true in practice
  (`agent/react.py` → `retrieval.pipeline.run_retrieval`) and is a legitimate
  functional dependency, not a layering violation — codifying it explicitly is more
  honest than leaving the original absolute wording in place and accumulating more
  silent exceptions to it.

`shared/` was previously documented as "only: logging.py, tracing.py" — that line
in `CLAUDE.md` was true when written and stopped being true the moment a type
needed to cross a slice boundary as data. It now reads "logging.py, tracing.py,
cli.py, types.py".

## Consequences

**Gain:**
- The "no cross-slice imports" rule in `CLAUDE.md` now matches the actual import
  graph — `grep -rn "^from rag\." src/rag/*/  | grep -v "rag\.\$(basename)\|backends\|shared"`
  returns only the legitimate `agent → retrieval` orchestration imports.
- `ingestion/types.py` shrinks to what it actually owns (`Document`,
  `DocumentMetadata`, `DocumentOutcome`, `IngestionResult`) — reading that file now
  tells you what's ingestion-specific without also showing types three other
  slices depend on.
- Future slices that need `Chunk`-shaped data (e.g. a hybrid-search slice) have an
  obvious place to import from, instead of a choice between "import from
  `ingestion` anyway" and "duplicate the type."

**Lose:**
- One more file to know about (`shared/types.py`) when first reading the codebase.
- `shared/` is no longer purely cross-cutting infrastructure concerns
  (logging/tracing) — it now also holds domain data shapes. This is a real
  loosening of what "shared" meant in the original `CLAUDE.md` wording, accepted
  because the alternative (duplicate types, or one slice silently owning a
  multi-slice contract) is worse.

**Technical debt:**
- `shared/types.py` can become a dumping ground if every future cross-slice type
  question gets answered with "put it in shared" instead of asking whether a type
  needs to exist in two slices at all. The test to apply before adding a type here:
  is it genuinely consumed as *data* by more than one slice (qualifies), or does
  only one slice's pipeline function get called by another slice that could pass a
  primitive instead (does not qualify — keep the type where the called slice
  defines it, have the caller pass primitives across the boundary).
