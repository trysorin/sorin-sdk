# sorin-sdk

Python SDK for the [Sorin](https://trysorin.com) agent authorization and observability platform.

## Install

```bash
pip install sorin-sdk
```

For local development:

```bash
pip install -e ./python
```

## Usage

### LLM Inference (Anthropic)

```python
from sorin import SorinLLM

client = SorinLLM(agent_key="your-agent-key")

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=100,
    messages=[{"role": "user", "content": "Hello"}]
)
```

### LLM Inference (OpenAI)

```python
from sorin import SorinOpenAI

client = SorinOpenAI(agent_key="your-agent-key")

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}]
)
```

### Agent Actions (GitHub, etc.)

```python
from sorin import SorinClient
import uuid

sorin = SorinClient(agent_key="your-agent-key")

# Typical agent loop pattern
request_id = str(uuid.uuid4())

plan = {
    "connector": "github",
    "action": "comment-pr",
    "resource_type": "pull_request",
    "resource_id": "org/repo#42",
}

# 1. Log the intent before acting
sorin.capture_intent(
    plan=plan,
    reasoning="Adding a review comment to summarize CI results",
    request_id=request_id,
)

# 2. Check authorization
auth = sorin.authorize(
    action=plan["action"],
    connector=plan["connector"],
    resource_id=plan["resource_id"],
    request_id=request_id,
)

if auth.get("allowed"):
    # 3. Perform the action
    ...
else:
    print(f"Blocked: {auth.get('reason')}")
```

## Links

- [trysorin.com](https://trysorin.com)
- [Documentation](https://trysorin.com/docs)
- [PyPI](https://pypi.org/project/sorin-sdk/)
- [GitHub](https://github.com/trysorin/sorin-sdk)
- [Dashboard](https://trysorin.com)
