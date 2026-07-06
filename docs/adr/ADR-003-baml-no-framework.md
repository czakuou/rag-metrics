# ADR-003: BAML as the LLM contract layer — no agent framework

## Status

Accepted

## Context

The agent slice requires two things from an LLM interaction layer:

1. **Structured outputs** — the ReAct loop must receive typed, validated responses
   from the LLM (thought, action, observation, final answer), not raw strings
   that need to be parsed with regex or `json.loads()` that can throw at runtime.

2. **Prompt management** — prompts must be versioned, testable, and decoupled from
   Python logic. A prompt change should not require touching business logic code.

The question is not only *which tool* to use for structured outputs, but also
*whether to adopt an agent framework* that bundles retrieval, memory, tool calling,
and orchestration into one package.

### Why an agent framework is tempting

LangChain, LlamaIndex, and PydanticAI all promise to "handle the hard parts":
tool calling, memory, multi-step reasoning, retrieval integration.
They have large communities and many tutorials.

### Why an agent framework is a liability here

A ReAct loop is a `while` loop with three steps: Thought → Action → Observation.
The core logic fits in ~50 lines of Python. Wrapping that in a framework means:

- **Debuggability disappears into abstractions.** When the agent misbehaves,
  the stack trace points into framework internals, not your code.
- **Every framework version bump is a risk.** LangChain has broken its API
  multiple times across minor versions. The project then becomes about keeping
  up with the framework, not building the system.
- **Frameworks couple retrieval, prompting, and orchestration.** Replacing one
  component (e.g. swapping the vector store) requires understanding how the
  framework wired them together, not just your own code.
- **Evals become harder.** To measure faithfulness, you need to intercept the
  exact context passed to the LLM. Frameworks often make this opaque.
- **The interview argument fails.** "We used LangChain" ends the conversation.
  "We implemented ReAct from scratch and here is why" starts one.

## Options considered

### Option A — BAML (Boundary)

BAML is a DSL for defining LLM function signatures with typed inputs and outputs.
It generates a Python client from `.baml` schema files.

```baml
// agent/baml/react.baml
class Thought {
  reasoning string
  action_needed bool
}

class Action {
  tool_name string
  tool_input string
}

class FinalAnswer {
  answer string
  citations string[]
}

function ReActStep(query: string, context: string, history: string) -> Thought | Action | FinalAnswer {
  client GPT4oMini
  prompt #"
    You are a RAG agent. Given a query and retrieved context, decide:
    - If you need more information: return an Action with the tool to call
    - If you have enough context: return a FinalAnswer with citations
    - Otherwise: return a Thought explaining your reasoning

    Query: {{ query }}
    Context: {{ context }}
    History: {{ history }}
  "#
}
```

The generated client (`baml_client`) handles:
- JSON schema injection into the prompt
- Response parsing and Pydantic model construction
- Retry on parse failure (configurable)
- Type validation — if the LLM returns an invalid structure, BAML raises before
  your code ever sees the response

**Cost model:** BAML is open source, self-hosted. No API beyond the LLM itself.
The generated client is plain Python — readable, debuggable, vendor-agnostic.

**Prompt versioning:** `.baml` files are committed to the repo. Prompt changes
are tracked in git history with diffs. No "prompt stored in a database" problem.

### Option B — PydanticAI

Python-first agent framework using Pydantic models as the output contract.
Structured outputs via `response_model` parameter.
Native async support. Clean API.

**Pros over BAML:**
- No DSL to learn — pure Python
- Strong Pydantic v2 integration
- Maintained by the Pydantic team (low abandonment risk)

**Cons:**
- Bundles agent orchestration, dependency injection, tool calling, and result
  validation into one package — the coupling that this project explicitly avoids
- Prompt lives in Python strings or decorated functions — not in version-controlled
  schema files with a diff-friendly format
- Output validation is Pydantic (good), but retry-on-parse-failure requires
  manual implementation
- Newer project — less production evidence than BAML

### Option C — LangChain (LCEL + structured output)

The dominant agent framework. Enormous ecosystem.

**Pros:**
- Most tutorials and Stack Overflow answers reference it
- Native integration with nearly every vector store, LLM, and tool

**Cons:**
- API instability: breaking changes across minor versions are documented in their
  own migration guides — a red flag for a production system
- Abstractions are leaky: `RunnableSequence`, `RunnableParallel`, `RunnableLambda`
  are concepts you must learn on top of the actual problem
- Structured output via `.with_structured_output()` is an abstraction over the
  LLM's native JSON mode — adds a layer of indirection that makes debugging harder
- Framework drives architecture: using LangChain correctly means thinking in
  LangChain's model of chains and agents, not in domain terms
- `langchain-community` is being sunset (as of 2025) — the ecosystem is fragmenting

### Option D — LlamaIndex

Purpose-built for RAG pipelines. Better retrieval abstractions than LangChain.

**Cons:**
- Same coupling problem: replacing pgvector means understanding LlamaIndex's
  storage abstraction, not your own
- Structured outputs require `llama-index-output-parsers` — an additional
  dependency with its own version surface
- The project already has a retrieval pipeline implemented as plain functions;
  LlamaIndex would replace it, not extend it

### Option E — Raw OpenAI function calling / JSON mode

Use the OpenAI SDK directly with `response_format={"type": "json_object"}` and
a Pydantic model for validation.

**Pros:**
- Zero new dependencies beyond the SDK
- Maximum control

**Cons:**
- Prompt construction is manual Python string concatenation — no schema file,
  no diff-friendly history
- No retry-on-parse-failure without manual implementation
- Couples the agent to OpenAI's API — contradicts the LiteLLM gateway principle
- JSON mode does not guarantee schema adherence — only that output is valid JSON.
  A missing required field passes JSON mode but fails Pydantic validation at runtime.

## Decision

Chose **Option A — BAML with no agent framework**.

The ReAct loop is implemented as a plain Python `while` loop in `agent/react.py`.
BAML handles the LLM contract: prompt definition, schema enforcement, and
retry-on-parse-failure. LiteLLM handles model routing and cost tracking.

### The concrete cost argument

Every agent framework adds a dependency that encodes *its author's opinions*
about how agents should work into your architecture. The cost of that opinion:

- You cannot replace one component without understanding the framework's wiring
- Stack traces during debugging point into framework code you did not write
- Eval instrumentation (intercepting context, logging tool calls) requires
  framework-specific hooks, not your own code

BAML's cost is narrow: it encodes opinions about *LLM output contracts*, nothing
else. It does not touch retrieval, orchestration, memory, or tool dispatch.
Those remain plain Python functions that any engineer can read and modify.

### Why BAML over raw JSON mode

BAML's DSL produces a git-diffable prompt history. When a prompt change causes
a RAGAS regression, `git log baml/` shows exactly what changed and when.
With raw string prompts in Python files, the diff is polluted by surrounding
code changes.

BAML also generates the Pydantic models from the schema — the type definitions
are the source of truth, not Python classes that might drift from the prompt.

### ReAct loop — the actual implementation shape

```python
# agent/react.py

from baml_client import b
from baml_client.types import Action, FinalAnswer, Thought
from rag.agent.types import AgentResult, Observation
from rag.retrieval.pipeline import run_retrieval


MAX_ITERATIONS = 5


def run_react_loop(query: str, config: Settings) -> AgentResult:
    history: list[str] = []
    iterations = 0

    while iterations < MAX_ITERATIONS:
        context = _build_context(history)
        step = b.ReActStep(query=query, context=context, history="\n".join(history))

        match step:
            case FinalAnswer():
                return AgentResult(answer=step.answer, citations=step.citations)
            case Action():
                observation = _dispatch_tool(step, config)
                history.append(f"Action: {step.tool_name}({step.tool_input})")
                history.append(f"Observation: {observation.result}")
            case Thought():
                history.append(f"Thought: {step.reasoning}")

        iterations += 1

    return AgentResult(answer="Max iterations reached.", citations=[])
```

This is the entire orchestration layer. No framework. No magic.
`b.ReActStep()` is the generated BAML client — one function call, fully typed.

## Consequences

**Gain:**
- ReAct loop is ~50 lines of readable Python — any engineer can understand and
  modify it without framework knowledge
- Prompt changes are git-diffable in `.baml` files — RAGAS regressions are traceable
- BAML handles retry-on-parse-failure — eliminates a class of runtime errors
  that occur when the LLM returns malformed JSON
- Swapping the LLM model is one line in `baml/clients.baml` (or via LiteLLM)
- Zero framework migration risk — BAML's scope is narrow enough that its API
  is stable

**Lose:**
- Learning the BAML DSL — approximately 2 hours for the subset used here
- No built-in memory, tool registry, or multi-agent coordination — must implement
  manually if needed (not in scope for v1)
- Smaller community than LangChain — fewer tutorials, but the BAML docs are
  comprehensive for this use case

**Files introduced:**

```
src/rag/agent/
├── baml_src/
│   ├── clients.baml      # LLM client config (model, temperature, retry)
│   ├── react.baml        # ReActStep function schema
│   └── generators.baml   # BAML generator config (output path, language)
├── baml_client/          # generated — do not edit manually, add to .gitignore
│   ├── __init__.py
│   └── types.py
```

`baml_client/` is generated from `baml_src/` by running `baml-cli generate`.
It is excluded from version control — generated on install via `make generate`.

**Add to Makefile:**

```makefile
generate:
	uvx baml-cli generate
```

**Add to `.gitignore`:**

```
src/rag/agent/baml_client/
```

**Technical debt:**
- `MAX_ITERATIONS = 5` is a hard-coded safety limit. If complex queries require
  more tool calls, this must be made configurable via `config.py`.
- BAML's retry behaviour on parse failure makes additional LLM calls — each retry
  costs money. Monitor via LangFuse traces if retry rate exceeds 10%.
