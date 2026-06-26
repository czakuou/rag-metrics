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
| pgvector            | Stateful `Protocol` (`VectorStoreBackend`) | `DATABASE_URL` |

See [ADR-004](docs/adr/ADR-004-swappable-backends.md) for the design rationale.

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
with RAGAS (`faithfulness`, `answer_relevancy`, `context_precision`), and compares them against the
thresholds in `src/rag/evals/thresholds.py` (sourced from `Settings` in `config.py`). If any metric
falls below its threshold, the CI gate fails. `data/baseline_scores.json` tracks the last known-good
scores — it must be updated in the same commit as any pipeline change, per the rules in `CLAUDE.md`.

## ADRs

- [ADR-001: Eval framework](docs/adr/ADR-001-eval-framework.md)
- [ADR-002: Evals-first development](docs/adr/ADR-002-evals-first.md)
- [ADR-003: Chunking strategy](docs/adr/ADR-003-chunking-strategy.md)
- [ADR-004: Swappable backends](docs/adr/ADR-004-swappable-backends.md)

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
