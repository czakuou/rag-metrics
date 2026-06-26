# ADR-001: RAGAS as the evaluation framework

## Status

Accepted

## Context

The core weakness identified in the InPost technical interview was the absence of
a principled approach to measuring RAG quality. The interviewer's feedback pointed
to gaps in: eval design, LLM measurement, and CI/CD integration for AI systems.

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
High implementation cost for a portfolio project where speed matters.
Harder to justify in an interview — no established metric definition to point to.

### Option D — Human evaluation only

No automation; a human reads outputs and scores them.
Cannot run in CI.
Not reproducible across pipeline versions.
Ruled out immediately — CI integration is a hard requirement.

## Decision

Chose **Option A — RAGAS**.

The RAG Triad maps directly to the three failure modes the InPost interviewer was
probing for. RAGAS is the reference implementation of those metrics; citing it in
an interview carries more weight than citing a custom script that does "something similar."

The LiteLLM integration means the eval LLM can be swapped via `.env` without
touching eval code — the same swappability principle used in the rest of the project.

The hosted-platform features of DeepEval are not needed. CI integration via
GitHub Actions requires only: run script → check numeric thresholds → exit 1 if below.
RAGAS supports this natively.

## Consequences

**Gain:**
- CI gate is a one-liner: `assert score >= THRESHOLDS["faithfulness"]`
- Metric definitions are citable in interviews and ADRs
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