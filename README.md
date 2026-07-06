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
└── shared/             # only: logging.py, tracing.py
```

Each slice is self-contained — read one folder, understand the entire domain. Slices never import
from each other directly; only `backends/` and `shared/` are shared dependencies.

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

`make eval` runs the agent over every example in `data/golden_dataset.jsonl`, scores the answers
with RAGAS (`faithfulness`, `answer_relevancy`, `context_precision`), and gates on two independent
checks against the thresholds and baseline in `src/rag/config.py`:

1. **Absolute threshold** — each metric must be `>= 0.85`.
2. **Regression vs. baseline** — each metric must not drop more than
   `eval_regression_tolerance` (0.02) below the matching value in
   `data/baseline_scores.json`.

`data/baseline_scores.json` only advances when a run passes both checks — a regressed run never
becomes the new reference. See `src/rag/evals/types.py::MetricScore` for the gating logic.

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
| [`evals.yml`](.github/workflows/evals.yml) | pull request to `main` | spins up Postgres + LiteLLM proxy, runs ingestion, then the RAGAS eval gate described above |

The split exists so the fast unit/type/lint loop runs on every push without paying for LLM-as-judge
calls, while the expensive RAGAS gate only runs where it matters — before code reaches `main`.

## ADRs

- [ADR-001: Eval framework](docs/adr/ADR-001-eval-framework.md)
- [ADR-002: Chunking strategy](docs/adr/ADR-002-chunking-strategy.md)
- [ADR-003: BAML as the LLM contract layer — no agent framework](docs/adr/ADR-003-baml-no-framework.md)
- [ADR-004: pgvector as the vector store](docs/adr/ADR-004-pgvector.md)
- [ADR-005: shared types instead of cross-slice imports](docs/adr/ADR-005-shared-types.md)

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
