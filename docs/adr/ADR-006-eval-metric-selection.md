# ADR-006: Eval metric selection and CI gate design

## Status

Accepted

## Context

ADR-001 chose RAGAS as the evaluation framework and established the RAG Triad as the
failure model. This ADR records the specific metric selection decisions within that
framework: which three metrics were chosen, which candidate metrics were rejected and
why, and why the CI gate uses two independent checks (absolute threshold + per-PR
regression) rather than one.

The project is a personal Obsidian vault assistant. That context matters for threshold
setting: the cost of a wrong answer is low (no downstream business logic, no users other
than the owner), but the cost of over-engineering the eval suite is real — running a
100-sample labeled dataset with GPT-4 to achieve 0.92 instead of 0.87 is not a
worthwhile trade for a private project.

## Metric selection

### Chosen metrics

Three metrics form the CI gate. Each maps to one failure mode:

| Failure mode | Metric | How it detects it |
|---|---|---|
| Hallucination | `faithfulness` | Decomposes the answer into claims, checks each against retrieved context via NLI. A claim not supported by context counts against the score. |
| Answer misalignment | `answer_relevancy` | Generates reverse questions from the answer, embeds them, and measures cosine similarity to the original question. A low score means the answer drifts off-topic. |
| Retrieval noise | `context_precision` | Checks whether the top-ranked retrieved chunks are the ones that actually contributed to the answer (using `reference` as the relevance signal). A low score means useful context is buried under irrelevant chunks. |

All three are LLM-as-judge metrics (RAGAS calls the eval LLM internally). None requires
a labeled "correct/incorrect" annotation — only a `reference` (ground truth answer),
which is already present in every `EvalSample`.

### Rejected metric: `context_recall`

`context_recall` measures what fraction of the ground truth answer is covered by the
retrieved context. It is referential and directional: it catches the case where retrieval
misses information the answer needed.

**Why rejected:**

The Obsidian vault is a personal, fragmentary knowledge base. Notes are written for the
owner's use, not as encyclopaedic articles — a concept may be mentioned across three
partial notes rather than in one definitive source. `context_recall` assumes that
`reference` (the ground truth answer) is fully derivable from some subset of the corpus.
That assumption does not hold here: the golden dataset questions were written to have
known answers, but the vault notes that support those answers are often incomplete or
written in a way that makes the NLI derivation unreliable.

The practical consequence: `context_recall` scores on this corpus had high variance and
were systematically lower than expected even on questions with correct answers, because
the vault phrasing rarely matched the reference phrasing closely enough for the RAGAS
judge to confirm derivability. A metric that fires on correct retrieval is not a useful
gate.

`context_precision` covers the complementary risk (noise in the retrieved set) without
this false-positive problem, and was already sufficient to catch the retrieval regression
documented in ADR-002.

### Rejected metric: BERTScore (hallucination alternative)

BERTScore measures semantic similarity between generated text and a reference. It is used
in some RAG evaluation setups as a hallucination proxy.

**Why rejected:**

Paraphrasing hallucination — where a model restates the context in slightly different
words while adding a fabricated detail — produces high BERTScore despite being
a real failure. RAGAS `faithfulness` uses NLI decomposition (claim-by-claim entailment
check), which catches this case. BERTScore does not have the resolution to distinguish
"mostly similar" from "fully grounded". For a knowledge-retrieval system where the key
risk is inventing facts, claim-level grounding is the right abstraction.

### Rejected metric: BLEU / ROUGE (answer quality alternatives)

BLEU and ROUGE measure n-gram overlap between generated and reference text.

**Why rejected:**

Personal notes have no single canonical phrasing. A correct answer to "What is the CAP
theorem?" can be written in many ways that share no n-grams with the ground truth while
being fully correct. Lexical overlap metrics are not meaningful for open-ended question
answering over informal text.

### Rejected approach: human evaluation only

Ruled out in ADR-001. Not reproducible, not runnable in CI.

## LLM-as-judge: design implications

All three chosen metrics are LLM-as-judge. This has two direct consequences on the
system design:

**1. Judge LLM is separate from the chat LLM (`llm_eval_model` ≠ `llm_chat_model`).**

A model judging its own outputs introduces self-evaluation bias: it is more likely to
find its own answers "faithful" and "relevant" than an independent judge would. The eval
model is configured separately in `config.py` and routed through the LiteLLM proxy under
a distinct alias (`eval-judge`), making it trivially swappable without touching eval
code.

**2. Judge non-determinism is a first-class concern.**

The same pipeline run will produce slightly different RAGAS scores across runs due to LLM
sampling variance. This makes a pure absolute-threshold gate unreliable as a regression
detector: a PR that truly regressed by 2pp might score above the threshold on one run and
below on the next. The CI gate design below addresses this directly.

## CI gate design: two independent checks

The gate runs two checks per metric, both of which must pass for CI to succeed:

### Check 1 — Absolute threshold (floor)

```
score >= 0.85
```

Catches catastrophic failures. On a first run (no baseline yet), this is the only check.
Threshold 0.85 was chosen as a practical floor for this project's cost and risk profile:
observed scores on the golden dataset are 0.91–0.94, so 0.85 gives a ~6–9pp buffer
before the gate fires. For a personal knowledge base where the consequence of a wrong
answer is low, a score of 0.85 represents acceptable quality without requiring the
labelling effort or compute cost needed to push baselines reliably above 0.90.

This is a deliberate tradeoff. Achieving consistent 0.90+ would require either a larger
golden dataset (more samples → more stable mean) or a better judge model (higher cost per
run). Neither is justified for a private project where the eval suite's primary value is
catching regressions, not certifying absolute quality.

### Check 2 — Regression against baseline (drift guard)

```
score >= baseline - 0.02
```

Catches slow degradation that stays above the absolute threshold. Without this check, a
metric could decline from 0.94 → 0.91 → 0.88 → 0.86 across four PRs, each passing CI
individually, with the system meaningfully worse by the end.

`data/baseline_scores.json` stores the last passing run's scores. The tolerance of 0.02
(2 percentage points) is sized to exceed typical RAGAS judge noise (~0.01pp run-to-run
variance observed on this corpus and judge model) while remaining tight enough to catch
a real pipeline regression on the next PR.

**Why two checks rather than one tighter threshold?**

A single threshold set at e.g. 0.90 would not work: on first run there is no history,
so the threshold would have to be set conservatively (low) to avoid blocking the first
passing commit. Raising the threshold post-hoc creates a chicken-and-egg problem: if
observed scores are 0.91, setting the threshold to 0.90 means any judge-noise run fails
CI. The two-check design separates the concerns cleanly — the absolute threshold is a
coarse floor, the regression check is the precision instrument.

### Baseline advancement rule

`data/baseline_scores.json` is only overwritten when `report.passed == True` (both
checks passed for all metrics). A run that regresses does not become the new reference,
which would silently reset the regression check to the degraded level and defeat its
purpose.

## Consequences

**Gain:**
- Each rejected alternative is documented with a specific failure mode it does not cover,
  not just "we chose something else"
- The two-gate structure means judge noise (which affects the regression check) and
  catastrophic failure (which the absolute threshold catches) are independently tunable
- Threshold at 0.85 keeps eval costs low: the gate is a real floor without requiring
  compute-intensive runs to maintain scores at 0.90+
- Judge is swappable via `.env` — upgrading to a cheaper or better judge model does not
  touch eval logic

**Lose:**
- `context_recall` is not measured. If the vault grows significantly and retrieval starts
  missing relevant notes entirely (not just ranking them low), this gap will not be caught
  by the current gate.
- 0.85 is calibrated to cost, not to a labeled error rate. "What fraction of answers
  below 0.85 are actually wrong?" is an open question. Answering it would require 20–30
  manually labeled samples — deferred until the project has production traffic.

**Technical debt:**
- If judge LLM is swapped to a model with different calibration, baseline scores are no
  longer comparable and must be reset. This is expected but must be done explicitly, not
  silently.
