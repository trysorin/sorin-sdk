import anthropic
from openai import OpenAI


class SorinLLM(anthropic.Anthropic):
    def __init__(self, agent_key: str, base_url: str = "https://sorin-eight.vercel.app", **kwargs):
        super().__init__(
            api_key=agent_key,
            base_url=f"{base_url.rstrip('/')}/api/runtime/llm",
            **kwargs
        )


class SorinOpenAI(OpenAI):
    def __init__(self, agent_key: str, base_url: str = "https://sorin-eight.vercel.app", **kwargs):
        super().__init__(
            api_key=agent_key,
            base_url=f"{base_url.rstrip('/')}/api/runtime/openai/v1",
            **kwargs
        )
