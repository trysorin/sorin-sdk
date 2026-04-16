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

sorin = SorinClient(agent_key="your-agent-key")

# Check authorization before acting (reasoning is optional)
auth = sorin.authorize(
    action="comment-pr",
    connector="github",
    resource_id="org/repo#42",
    reasoning="Adding a review comment to summarize CI results",
)

if auth.get("allowed"):
    # Perform the action
    ...
else:
    print(f"Blocked: {auth.get('reason')}")
```

### Tool calls grouped by LLM turn

The Activity dashboard groups your agent's tool calls under the LLM turn that triggered them. No setup required — the SDK handles it when you use `SorinLLM`/`SorinOpenAI` and `SorinClient` together.

If a single LLM turn fires multiple parallel tool calls, opt into finer-grained labeling by passing the block id:

```python
response = sorin_llm.messages.create(model=..., messages=..., tools=...)
for block in response.content:
    if block.type == "tool_use":
        sorin.github.push_file(**block.input, tool_use_id=block.id)
```

`tool_use_id` is optional on every `sorin.github.*` method.

## MCP Server

The package ships a `sorin` CLI that connects any MCP-compatible AI coding tool to the Sorin MCP server.

**Claude Code** — registers the server automatically:
```bash
sorin mcp install --key <your-sorin-agent-key>
```

**Cursor, Windsurf, VS Code, or any host that uses `mcpServers` JSON config** — prints the config block to paste in:
```bash
sorin mcp install --key <your-sorin-agent-key> --json
```

Config file locations:
- Cursor: `~/.cursor/mcp.json`
- Windsurf: `~/.codeium/windsurf/mcp_config.json`
- VS Code: `.vscode/mcp.json` (workspace) or user settings

Restart your editor after installing to connect.

## Links

- [trysorin.com](https://trysorin.com)
- [Documentation](https://trysorin.com/docs)
- [PyPI](https://pypi.org/project/sorin-sdk/)
- [GitHub](https://github.com/trysorin/sorin-sdk)
- [Dashboard](https://trysorin.com)
