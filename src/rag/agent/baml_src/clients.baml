// LLM client for the ReAct loop. Temperature is low — the agent must be
// deterministic, not creative — and retries cover transient parse failures.
// Routed through the LiteLLM proxy — cost tracking and fallback happen there.
client<llm> AgentLLM {
  provider openai
  retry_policy ReActRetry
  options {
    model env.LLM_CHAT_MODEL
    api_key env.LITELLM_MASTER_KEY
    base_url env.LITELLM_BASE_URL_LOCAL
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
