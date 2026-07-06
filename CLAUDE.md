# CLAUDE.md — agent instructions

> Read this file in full before writing anything.
> Return to it when you are unsure about a design decision.

---

## Language rules

- **All code, comments, docstrings, ADRs, and documentation must be written in English.**
- The user may communicate with you in Polish — that is fine. Respond in Polish if they write in Polish.
- Never mix languages inside a single file. Polish conversation, English artefacts — always.

---

## What this project is

Agentic RAG system built on a private Obsidian vault.
Stack: Python 3.13+, pgvector, LiteLLM, BAML, RAGAS, GitHub Actions.
Philosophy: **evals-first** — every pipeline change is measurable via a CI gate.

---

## Project structure — vertical slices

```
src/rag/
├── config.py           # Pydantic Settings — single source of configuration
├── ingestion/          # slice: vault → chunks → vector store
├── retrieval/          # slice: query → rerank → grade
├── agent/              # slice: ReAct loop → answer
├── evals/              # slice: golden dataset → RAGAS → CI gate
├── backends/           # swappable: embedding/, vectorstore/
└── shared/             # logging.py, tracing.py, cli.py, types.py
```

**Rule:** each slice is self-contained. Read one folder — understand the entire domain.

Every slice contains:
- `types.py` — domain types owned by this slice
- `pipeline.py` — main function invoked by CLI (`python -m rag.<slice>.pipeline`)
- domain function files (`loader.py`, `chunker.py`, etc.)

### Cross-slice imports — what's allowed and why

Two kinds of cross-slice dependency are legal; both are imports, but they mean
different things, and confusing them is how this rule gets violated by accident:

1. **A slice imports another slice's domain function/pipeline to orchestrate it.**
   Example: `agent/react.py` imports `retrieval.pipeline.run_retrieval`. The agent
   *calls* retrieval as a step in the ReAct loop — that's a real functional
   dependency, not a layering violation. This is allowed for slices that are
   explicitly downstream of another in the data flow (`agent` depends on
   `retrieval`, never the reverse).
2. **Two slices need the same domain type because one produces it and another
   consumes it as data**, not by calling into the producing slice's functions.
   Example: `ingestion` produces `Chunk`/`EmbeddedChunk`, `retrieval` and
   `backends/vectorstore` consume them as data. Importing `Chunk` from
   `rag.ingestion.types` here would be wrong — it isn't really an "ingestion
   type" once two other slices depend on it, and it tempts `ingestion/types.py`
   to grow business logic that `retrieval` then has no business reading. The
   type belongs in `rag.shared.types` instead — see [ADR-005](docs/adr/ADR-005-shared-types.md).

If you find yourself importing a *type* (not a pipeline/orchestration function)
across slice boundaries, that is the signal to move the type to `shared/types.py`,
not to leave the cross-slice import in place.

---

## Code style — functional core

### Write functions, not classes

```python
# ✅ DO
def chunk(doc: Document, strategy: ChunkStrategy) -> list[Chunk]:
    match strategy:
        case ChunkStrategy.FIXED:        return _fixed_size(doc)
        case ChunkStrategy.PARENT_CHILD: return _parent_child(doc)
        case ChunkStrategy.SEMANTIC:     return _semantic(doc)

# ❌ DON'T
class ChunkerService:
    def __init__(self, strategy: ChunkStrategy) -> None:
        self.strategy = strategy
    def chunk(self, doc: Document) -> list[Chunk]:
        ...
```

Exceptions:
- Pydantic models (data types) → always classes
- **Value Objects** (Pydantic models representing a domain concept, not just a data bag) →
  always classes, and they may carry domain logic — see "Value Objects" below
- Pydantic Settings (config) → always a class
- Backends → `Protocol` if the backend is stateful, callable if stateless

### Swappable backends — two patterns

**Stateless backend = plain callable (preferred)**

```python
# backends/embedding/protocol.py
from collections.abc import Callable

type EmbedFn = Callable[[list[str]], list[list[float]]]

# backends/embedding/openai_backend.py
from rag.backends.embedding.protocol import EmbedFn

def make_openai_backend(model: str = "text-embedding-3-small") -> EmbedFn:
    def embed(texts: list[str]) -> list[list[float]]:
        ...  # call OpenAI API
    return embed
```

**Stateful backend = Protocol (when you need a connection pool, cache, etc.)**

```python
# backends/vectorstore/protocol.py
from typing import Protocol

class VectorStoreBackend(Protocol):
    def upsert(self, chunks: list[EmbeddedChunk]) -> None: ...
    def search(self, vector: list[float], k: int) -> list[Chunk]: ...
    def delete(self, ids: list[str]) -> None: ...
```

Business logic (retrieval, ingestion) never imports concrete backends — only the type from `protocol.py`.
The backend is injected from `config.py` at the `pipeline.py` level.

### Value Objects — push domain logic into the type, not a function next to it

If a value has an invariant (e.g. "passed is always derived from score and threshold") or a
collection of values needs the same operation applied to all of them (e.g. "all metrics passed",
"which questions failed any metric"), that belongs on the type as a property or method — not as
a loose function in a sibling module that reads the type's fields from outside.

This keeps the invariant impossible to violate (you cannot construct an inconsistent `passed`
because it is computed, never stored) and hides iteration behind a name that says what the loop
means, instead of a bare `for` a caller has to re-read every time.

```python
# ✅ DO — the invariant lives on the type; "passed" can never disagree with score/threshold
class MetricScore(BaseModel):
    name: str
    score: float
    threshold: float

    @property
    def passed(self) -> bool:
        return self.score >= self.threshold

# A composite Value Object hides the loop over individual Value Objects.
class MetricScores(BaseModel):
    scores: list[MetricScore]

    @property
    def all_passed(self) -> bool:
        return all(metric_score.passed for metric_score in self.scores)

# ❌ DON'T — passed is a plain field set by a function elsewhere; nothing stops it
# from drifting out of sync with score/threshold, and "all passed" is a loop the
# caller has to write (and get right) every time it's needed.
class MetricScore(BaseModel):
    name: str
    score: float
    passed: bool  # set by score_report() — could be wrong, nothing enforces it

def all_passed(scores: list[MetricScore]) -> bool:
    return all(s.passed for s in scores)
```

A plain function is still right for *composing* Value Objects (turning an external result into
domain types) — that is orchestration, not domain logic, and the "one function, one
responsibility" rule below still applies to it.

### One function, one responsibility

A function does one thing: fetch data, transform data, or produce a side effect (I/O, print, write).
Never two of these at once. If a function both calls an external boundary (LLM, DB, pipeline_fn)
*and* computes a result from it, split it: one function to fetch, one pure function to compute.

```python
# ✅ DO — fetch is its own function; computing the report is delegated to Value Objects
# (MetricScores, EvalReport), so score_report only orchestrates, it doesn't loop or decide.
def build_evaluation_dataset(samples: list[Sample], pipeline_fn: PipelineFn) -> Dataset: ...

def score_report(dataset: Dataset, result: RagasResult, thresholds: dict[str, float]) -> Report:
    metric_scores = MetricScores.from_ragas_result(result, thresholds)
    return EvalReport.from_metric_scores(metric_scores, ...)

def run_evals(samples, pipeline_fn, thresholds) -> Report:
    dataset = build_evaluation_dataset(samples, pipeline_fn)
    result = evaluate(dataset)
    return score_report(dataset, result, thresholds)

# ❌ DON'T — one function runs the pipeline AND aggregates scores AND decides pass/fail
def run_evals(samples, pipeline_fn, thresholds) -> Report:
    for sample in samples: ...        # fetch
    result = evaluate(...)
    for metric in metrics: ...        # compute + decide, mixed into the same function
```

Same rule applies to CLI output: formatting (pure, string in → string out) is never mixed with
printing (`print`) or writing files. Put formatting helpers in `shared/` if more than one
slice needs them (e.g. `shared/cli.py::render_table`); keep them in the slice if only one
pipeline.py consumes them.

```python
# ✅ DO
def render_table(headers: list[str], rows: list[list[str]]) -> str: ...   # shared/cli.py, pure
print(render_table(headers, rows))                                        # pipeline.py, the only print

# ❌ DON'T — formatting and the print() are fused, can't be tested without capturing stdout
def _print_summary(report: Report) -> None:
    print(f"| {report.metric:<25} | ...")
```

---

## Typing — mandatory, complete

### Rules

- Every public function has full type annotations: arguments + return type
- No `Any` without a `# type: ignore[...]` comment with a reason
- No bare `dict` as a domain type — always a Pydantic model or TypedDict
- Use the `type` statement (Python 3.12+) for type aliases that appear more than once

```python
# ✅ DO
from pydantic import BaseModel

type EmbeddingVector = list[float]
type ChunkBatch = list[Chunk]

class Chunk(BaseModel):
    id: str
    content: str
    metadata: ChunkMetadata
    embedding: EmbeddingVector | None = None

def embed(chunks: ChunkBatch, backend: EmbedFn) -> ChunkBatch:
    ...

# ❌ DON'T — legacy syntax
from typing import TypeAlias
EmbeddingVector: TypeAlias = list[float]

# ❌ DON'T
def embed(chunks, backend):
    ...

# ❌ DON'T
def embed(chunks: list[dict], backend: Any) -> list[dict]:
    ...
```

### Where types live

Domain types for a slice → `<slice>/types.py`
Types shared across slices → they don't exist (that's a signal you need a new slice)
Exception: types from `backends/*/protocol.py` are imported by `pipeline.py` in slices

---

## Tests — BDD, no mocks, no implementation details

### Philosophy

Test **behaviour**, not implementation.
If you refactor internal logic without changing the contract → tests must not break.

### Test structure: Given / When / Then

```python
# tests/ingestion/test_chunker.py
from rag.ingestion.chunker import chunk
from rag.ingestion.types import Chunk, ChunkStrategy, Document, DocumentMetadata


def test_fixed_chunker_splits_long_document_into_multiple_chunks():
    # Given
    long_document = Document(
        content="word " * 2000,  # 2000 words — guaranteed to exceed chunk limit
        metadata=DocumentMetadata(source="vault/test.md"),
    )

    # When
    chunks = chunk(long_document, strategy=ChunkStrategy.FIXED)

    # Then
    assert len(chunks) > 1
    assert all(isinstance(c, Chunk) for c in chunks)
    assert all(len(c.content.split()) <= 600 for c in chunks)  # max 512 + overlap


def test_chunker_preserves_document_source_in_metadata():
    # Given
    doc = Document(
        content="A short note about RAG.",
        metadata=DocumentMetadata(source="vault/rag.md"),
    )

    # When
    chunks = chunk(doc, strategy=ChunkStrategy.FIXED)

    # Then
    assert all(c.metadata.source == "vault/rag.md" for c in chunks)
```

### What NOT to test

```python
# ❌ Never test private functions
from rag.ingestion.chunker import _fixed_size  # NEVER

# ❌ Never assert that a specific method was called
mock_backend.embed.assert_called_once_with(...)  # NEVER

# ❌ Never mock what you can build
@patch("rag.ingestion.chunker.SomeInternalClass")  # NEVER

# ❌ Never inspect internal state
assert chunks[0]._internal_state == "processed"  # NEVER
```

### When a mock is acceptable

Only at the boundary of infrastructure you do not control:
- External APIs (OpenAI, LangFuse) — use `respx` or `pytest-httpx`
- Database — use a real test database (Docker), not a mock

```python
# ✅ Acceptable mock — HTTP boundary with an external API
import httpx
import respx

@respx.mock
def test_openai_backend_returns_embedding_vectors():
    respx.post("https://api.openai.com/v1/embeddings").mock(
        return_value=httpx.Response(200, json={"data": [{"embedding": [0.1, 0.2, 0.3]}]})
    )
    ...
```

### Test naming

Format: `test_<what>_<condition>_<expected_result>`

```python
# ✅
def test_reranker_returns_chunks_sorted_by_relevance_score(): ...
def test_grader_marks_chunk_as_irrelevant_when_score_below_threshold(): ...
def test_react_loop_stops_after_max_iterations(): ...

# ❌
def test_reranker(): ...
def test_chunk_1(): ...
def test_it_works(): ...
```

---

## Documentation — when and what to update

### After every change, check:

| What you changed | What to update |
|---|---|
| New slice or removed slice | `README.md` (structure section) + `CLAUDE.md` (tree) |
| New design decision (new backend, new metric, strategy change) | `docs/adr/ADR-XXX-<topic>.md` (new ADR) |
| Threshold change in `evals/thresholds.py` | inline comment with reason + update `data/baseline_scores.json` |
| New variable in `config.py` | `.env.example` — always updated in the same commit |
| CLI change (new command, new argument) | `README.md` "How to run" section |
| New backend (embedding or vectorstore) | `docs/adr/` + `README.md` "Backends" section |

### ADR format

File: `docs/adr/ADR-NNN-<slug>.md`

```markdown
# ADR-NNN: <Title>

## Status
Accepted | Deprecated | Superseded by ADR-XXX

## Context
What triggered this decision? What were the constraints?

## Options considered
- Option A — short description
- Option B — short description

## Decision
Chose Option A because ...

## Consequences
What do we gain? What do we lose? What technical debt are we taking on?
```

---

## Rules never to break

1. **No untyped code** — mypy must pass clean
2. **No slice without `types.py`** — domain types are documentation
3. **No pipeline change without updating `data/baseline_scores.json`** — you must know if you regressed
4. **No `utils/` or `helpers/`** — name what it does or put it in `shared/`
5. **No cross-slice *type* imports** — a type used by more than one slice lives in
   `shared/types.py`, not in whichever slice happened to define it first. Importing
   another slice's *pipeline/orchestration function* (e.g. `agent` calling
   `retrieval.pipeline.run_retrieval`) is allowed — see "Cross-slice imports" above.
6. **Commit after every completed slice** — repo history is documentation for the recruiter
7. **`.env.example` always current** — new Settings variable = immediate update in the same commit

---

## Quick reference

```bash
# Run ingestion
make ingest

# Run evals (same as CI)
make eval

# Run agent interactively
make agent

# Type check
make typecheck   # uv run mypy src/

# Run tests
make test        # uv run pytest tests/ -v
```