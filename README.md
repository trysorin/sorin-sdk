# Sorin SDK

Official SDKs for the Sorin agent authorization and observability platform.

## Quick Start

### LLM Inference (Anthropic)

```python
# Before — no visibility
import anthropic
client = anthropic.Anthropic(api_key="sk-ant-...")

# After — full audit trail in Sorin, zero other changes
from sorin import SorinLLM
client = SorinLLM(agent_key="<sorin-agent-key>")

# Everything else stays identical
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=100,
    messages=[{"role": "user", "content": "Hello"}]
)
```

### LLM Inference (OpenAI)

```python
# Before
from openai import OpenAI
client = OpenAI(api_key="sk-...")

# After
from sorin import SorinOpenAI
client = SorinOpenAI(agent_key="<sorin-agent-key>")
```

### Agent Actions (GitHub, etc.)

```python
from sorin import SorinClient

sorin = SorinClient(agent_key="<sorin-agent-key>")
sorin.capture_intent(plan={...}, reasoning="...")
auth = sorin.authorize(action="list-pulls", connector="github", resource_id="org/repo")
```

## Packages

- [`python/`](./python) — Python SDK (`pip install sorin-sdk`)
- `js/` — JavaScript/TypeScript SDK (coming soon)

## Links

- [trysorin.com](https://trysorin.com)
- [Documentation](https://trysorin.com/docs)
