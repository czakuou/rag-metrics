// ReAct step contract: the LLM either reasons (Thought), calls a tool (Action),
// or answers (FinalAnswer). Python orchestrates the loop in agent/react.py —
// this file only defines the LLM-facing schema and prompt.

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
  client AgentLLM
  prompt #"
    You are a RAG agent answering questions over a private Obsidian vault.

    Given the query, the most recent retrieved context, and the reasoning
    history so far, decide what to do next:

    - If you need more information to answer the query, return an Action with
      tool_name = "vector_search" and tool_input = the search query to run.
    - If the retrieved context is sufficient to answer, return a FinalAnswer.
      Always cite the source note filenames you relied on in `citations`.
    - Otherwise, return a Thought explaining your reasoning before acting.

    Never invent information that is not present in the retrieved context.
    If the context does not contain the answer, say so in the FinalAnswer
    rather than guessing.

    Query: {{ query }}

    Most recent retrieved context:
    {{ context }}

    Reasoning history so far:
    {{ history }}

    {{ ctx.output_format }}
  "#
}

test react_step_answers_with_sufficient_context {
  functions [ReActStep]
  args {
    query "What is the capital of France?"
    context "note.md: Paris is the capital of France."
    history ""
  }
}
