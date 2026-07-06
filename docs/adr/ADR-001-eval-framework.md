# ADR-001: RAGAS as the evaluation framework

## Status

Accepted

## Context

RAG systems fail silently: a pipeline change can degrade answer quality without
throwing an exception anywhere. Without a principled way to measure retrieval and
generation quality, regressions are only caught by manually reading outputs — which
does not scale and is not reproducible across pipeline versions.

The project needs an eval framework that can:
- Measure retrieval and generation quality independently
- Run automatically in CI on every pull request
- Produce numeric scores that can be compared across pipeline versions
- Support a "golden dataset" workflow: fixed Q/A pairs, deterministic measurement

The framework must cover the RAG Triad — the three failure modes of RAG systems:
- **Faithfulness** — does the answer contradict the retrieved context? (hallucination)
- **Answer relevancy** — does the answer address the question? (off-topic output)
- **Context precision** — was the retrieved context actually useful? (retrieval noise)

## Options considered

### Option A — RAGAS

Open-source Python library purpose-built for RAG evaluation.
Implements the RAG Triad metrics natively.
Works with any LLM via LiteLLM integration.
Outputs numeric scores (0.0–1.0) that CI can threshold against.
Supports async evaluation for speed.
Has an active community and is referenced in production AI engineering literature.

**Cost:** each eval run calls the LLM to judge faithfulness — approximately $0.01–0.05
per sample depending on model and context length.

### Option B — DeepEval

Broader evaluation framework covering LLMs beyond RAG.
Has a hosted platform (Confident AI) with dashboards.
More complex setup; the hosted platform requires a paid account for CI integration.
The extra breadth (toxicity, bias, summarisation metrics) is not needed here.

**Cost:** same LLM-as-judge cost as RAGAS, plus platform fee for CI features.

### Option C — Custom eval scripts with direct LLM calls

Full control; no dependency on a third-party framework.
Requires implementing metric logic from scratch (NLI for faithfulness, cosine similarity
for relevancy, etc.).
High implementation cost relative to adopting an existing, validated framework.
No established, citable metric definition — harder to reason about whether a given
score is "good" without a reference implementation to compare against.

### Option D — Human evaluation only

No automation; a human reads outputs and scores them.
Cannot run in CI.
Not reproducible across pipeline versions.
Ruled out immediately — CI integration is a hard requirement.

## Decision

Chose **Option A — RAGAS**.

The RAG Triad maps directly to the three failure modes this project needs to guard
against. RAGAS is the reference implementation of those metrics, with a stable
definition that a custom script doing "something similar" would not have.

The LiteLLM integration means the eval LLM can be swapped via `.env` without
touching eval code — the same swappability principle used in the rest of the project.

The hosted-platform features of DeepEval are not needed. CI integration via
GitHub Actions requires only: run script → check numeric thresholds → exit 1 if below.
RAGAS supports this natively.

## Consequences

**Gain:**
- CI gate is a one-liner: `assert score >= THRESHOLDS["faithfulness"]`
- Metric definitions are standard and well-documented, not ad hoc
- Eval cost is predictable and low (~$0.02 per full suite run on gpt-4o-mini)
- Scores in `data/baseline_scores.json` give a permanent record of pipeline evolution

**Lose:**
- Eval runs cost money (LLM-as-judge) — mitigated by running only on PR to main,
  not on every push
- RAGAS metrics are not ground truth; they are LLM-judged approximations.
  A low faithfulness score means "the judge LLM thinks there is a contradiction",
  not a formally proven contradiction.

**Technical debt:**
- `data/baseline_scores.json` must be updated manually after every intentional
  threshold change. If it drifts from reality, CI becomes meaningless.

## Addendum: CI gate now checks regression, not just absolute threshold (2026-06-30)

The original CI gate only asserted `score >= threshold`, with thresholds (0.65–0.70)
set well below real scores (~0.90+). This meant the gate caught catastrophic failures
but not regressions — a change that dropped `context_precision` from 0.94 to 0.72
would still pass. This gap was not theoretical: it is exactly what happened when
`ChunkStrategy.PARENT_CHILD` was briefly made the default (see ADR-002 addendum) and
merged despite regressing two of three metrics, because nothing compared the new run
against `data/baseline_scores.json`.

**Fix:** `MetricScore.regressed` (in `evals/types.py`) now fails a metric if its score
drops more than `eval_regression_tolerance` (default 0.02) below the corresponding
value in `data/baseline_scores.json`, independently of the absolute threshold. The
threshold was also raised to 0.85 across all three metrics — close enough to observed
scores (~0.90+) that it acts as a real floor, not just a catastrophe check. The
regression check and the absolute threshold are deliberately both kept: the threshold
catches a bad first run (no baseline yet), the regression check catches a slow decline
across many merged PRs where each individual drop stays above 0.85.

`data/baseline_scores.json` is only overwritten when the run passes — a regressed run
must not become the new reference for the next PR's comparison.