// LLM client for the ReAct loop. Temperature is low — the agent must be
// deterministic, not creative — and retries cover transient parse failures.
client<llm> AgentLLM {
  provider openai
  retry_policy ReActRetry
  options {
    model env.LLM_MODEL
    api_key env.OPENAI_API_KEY
    temperature 0.1
  }
}

retry_policy ReActRetry {
  max_retries 2
  strategy {
    type constant_delay
    delay_ms 200
  }
}
