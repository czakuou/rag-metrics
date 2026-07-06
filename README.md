# obsidian-rag

## What this is

An agentic RAG system built on a private Obsidian vault. A ReAct agent retrieves and reasons over
notes from the vault to answer questions, with retrieved context reranked and graded before it
reaches the agent. The project follows an **evals-first** philosophy: every change to ingestion,
retrieval, or the agent loop is measured against a golden dataset with RAGAS metrics, and a CI gate
blocks merges that regress answer quality below the thresholds defined in `evals/thresholds.py`.

## Architecture

```
src/rag/
├── config.py           # Pydantic Settings — single source of configuration
├── ingestion/          # slice: vault → chunks → vector store
├── retrieval/          # slice: query → rerank → grade
├── agent/              # slice: ReAct loop → answer
├── evals/              # slice: golden dataset → RAGAS → CI gate
├── backends/           # swappable: embedding/, vectorstore/
└── shared/             # logging.py, tracing.py, llm.py, cli.py, types.py
```

Each slice is self-contained — read one folder, understand the entire domain. Cross-slice imports
are restricted: a downstream slice may call an upstream slice's pipeline function (e.g. `agent`
imports `retrieval.pipeline`), but types shared between slices live in `shared/types.py` rather
than in either slice. See [ADR-005](docs/adr/ADR-005-shared-types.md) for the rule and rationale.

## Backends

| Backend            | Type      | Env var to swap       |
|---------------------|-----------|------------------------|
| OpenAI embeddings   | Stateless callable (`EmbedFn`) | `EMBEDDING_BACKEND=openai` |
| pgvector            | Stateful `Protocol` (`VectorStoreBackend`), via SQLAlchemy Core async | `VECTORSTORE_BACKEND=pgvector`, `DATABASE_URL` |

See [ADR-004](docs/adr/ADR-004-pgvector.md) for the design rationale, including why
the vector store client is SQLAlchemy Core async rather than raw `asyncpg`.

## How to run

```bash
git clone <repo-url>
cd obsidian-rag
cp .env.example .env        # fill in OPENAI_API_KEY and Postgres credentials
make install                 # uv sync + pre-commit install
make up                      # docker compose up -d (Postgres + pgvector)
make ingest                  # vault → chunks → vector store
make eval                    # run the eval suite against the golden dataset
```

Run the agent interactively with `make agent`.

## Running evals

`make eval` runs **two gates** over every example in `data/golden_dataset.jsonl`, scoring answers
with RAGAS (`faithfulness`, `answer_relevancy`, `context_precision`):

| Gate | Command | Pipeline under test | Baseline file |
|---|---|---|---|
| Component | `make eval-retrieval` | retrieval → rerank → grade → single synthesis call | `data/baseline_scores.json` |
| End-to-end | `make eval-agent` | the actual ReAct agent (BAML loop + tool dispatch) | `data/agent_baseline_scores.json` |

The component gate isolates retrieval changes through the least noisy pipeline that exercises
them; the end-to-end gate measures what users actually get. When the end-to-end gate fails, the
component gate answers the first diagnostic question — "did retrieval regress, or did the
agent?" — for free. Full rationale in
[ADR-006](docs/adr/ADR-006-eval-metric-selection.md#addendum-two-eval-levels-and-pipeline-error-gating-2026-07-06).

Each gate applies three independent checks against the thresholds in `src/rag/config.py`:

1. **Absolute threshold** — each metric must be `>= 0.85`.
2. **Regression vs. baseline** — each metric must not drop more than
   `eval_regression_tolerance` (0.02) below the matching value in that gate's baseline file.
3. **No pipeline errors** — a sample that crashes the pipeline is excluded from the metric
   means, so errors fail the gate directly; otherwise a partially-broken pipeline could pass
   on the samples that survived.

A baseline file only advances when a run passes all checks — a regressed or partially-errored
run never becomes the new reference. See `src/rag/evals/types.py::MetricScore` and
`EvalReport.passed` for the gating logic.

**Sample size caveat:** the golden dataset is 25 questions. At that size, a single changed
answer moves a metric's mean by ~4 percentage points — comparable to the 0.02 regression
tolerance itself. The gate is sized to catch the kind of regression this repo has actually
hit (the parent-child chunking revert below, a ~0.018 drop), not to give strong statistical
confidence at smaller deltas. Treat a borderline regression-check failure as a prompt to look
at `failed_samples` in the eval report, not as ground truth on its own.

### Chunking strategy: measured, not assumed

The default chunking strategy is `fixed` (512 tokens, 64 overlap). `parent_child` was tried as the
default and measured against the same 25-sample golden dataset:

| Metric             | Fixed (current default) | Parent-child | Delta   |
|---------------------|--------------------------|--------------|---------|
| faithfulness        | 0.9146                   | 0.9039       | -0.0107 |
| answer_relevancy     | 0.9176                   | 0.9218       | +0.0042 |
| context_precision    | 0.9373                   | 0.9193       | -0.0180 |

Parent-child regressed `faithfulness` and `context_precision` — the latter is the exact metric it
was meant to improve — so the default was reverted to `fixed`. Full writeup, including why the
regression likely happened, is in [ADR-002](docs/adr/ADR-002-chunking-strategy.md#addendum-parent-child-measured-and-reverted-2026-06-30).
`ChunkStrategy.PARENT_CHILD` stays implemented and available for future experiments; it is just not
the default.

## CI

Two independent GitHub Actions pipelines:

| Workflow | Trigger | What it runs |
|---|---|---|
| [`tests.yml`](.github/workflows/tests.yml) | every push, any branch | `mypy`, `ruff check`, and unit tests (`pytest -m "not integration"`) — fast, no real LLM or DB calls |
| [`evals.yml`](.github/workflows/evals.yml) | pull request to `main` | spins up Postgres + LiteLLM proxy, runs ingestion, then **both** RAGAS eval gates described above (component + end-to-end agent) |

The split exists so the fast unit/type/lint loop runs on every push without paying for LLM-as-judge
calls, while the expensive RAGAS gate only runs where it matters — before code reaches `main`.

### Known cost optimisations not yet implemented

The current eval gate runs on every PR to `main` regardless of what changed. Three improvements
are worth considering as the project grows:

**Path-scoped triggers.** `evals.yml` could use GitHub Actions `paths:` filtering to skip the
eval run when only documentation, tests, or non-pipeline code changed — for example:

```yaml
on:
  pull_request:
    branches: [main]
    paths:
      - "src/rag/ingestion/**"
      - "src/rag/retrieval/**"
      - "src/rag/agent/**"
      - "src/rag/backends/**"
      - "data/golden_dataset.jsonl"
```

A change that only touches `README.md` or `tests/` would then skip the ~$0.04 RAGAS run (two
gates) entirely.
The tradeoff: a `config.py` threshold change or a `shared/` refactor that silently affects pipeline
behaviour would also be skipped unless `paths:` is kept up to date — creating a maintenance burden
that must be weighed against the cost saving.

**RAGAS result caching.** Each sample in the golden dataset produces a deterministic
`(question, retrieved_contexts, answer)` triple for a given pipeline state. If those inputs have
not changed since the last run, the RAGAS judge score cannot change either. A content-hash cache
keyed on that triple would let unchanged samples skip the LLM judge call entirely, making the
per-PR cost proportional to how many samples were actually affected by the change rather than the
full dataset size. Not implemented: adds complexity and a cache invalidation surface.

**Parallel RAGAS evaluation.** `ragas.evaluate()` supports async evaluation (`is_async=True`),
which would run the ~75 judge calls per gate (25 samples × 3 metrics) concurrently instead of
sequentially. At 25 samples this is not a bottleneck, but at 200+ samples the wall-clock time
difference becomes meaningful. Not enabled: the current sequential mode is simpler to reason about
and debug when a judge call fails.

## ADRs

- [ADR-001: Eval framework](docs/adr/ADR-001-eval-framework.md)
- [ADR-002: Chunking strategy](docs/adr/ADR-002-chunking-strategy.md)
- [ADR-003: BAML as the LLM contract layer — no agent framework](docs/adr/ADR-003-baml-no-framework.md)
- [ADR-004: pgvector as the vector store](docs/adr/ADR-004-pgvector.md)
- [ADR-005: shared types instead of cross-slice imports](docs/adr/ADR-005-shared-types.md)
- [ADR-006: Eval metric selection and CI gate design](docs/adr/ADR-006-eval-metric-selection.md)

## Development

```bash
make test         # uv run pytest tests/ -v
make typecheck     # uv run mypy src/
make lint          # uv run ruff check src/ tests/
make format        # uv run ruff format src/ tests/
make pre-commit    # uv run pre-commit run --all-files
```

Tests follow Given/When/Then behavioral style with no mocks except at infrastructure boundaries —
external APIs via `respx`, and the Postgres/pgvector database via `testcontainers` (see
`tests/conftest.py`).
