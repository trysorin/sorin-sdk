# Sorin Python SDK

## Installation

```
pip install sorin-sdk
```

or for local development:

```
pip install -e /path/to/sorin-sdk
```

## Quick Start

### Governed GitHub actions

```python
# Every call handles intent capture, authorization, and execution in one shot
from sorin import SorinClient

sorin = SorinClient(agent_key="<your-sorin-agent-key>")

sorin.github.read_file("org", "repo", "README.md")
sorin.github.create_branch("org", "repo", "my-feature")
sorin.github.push_file("org", "repo", "file.md", "# Hello", "add file", "my-feature")
pr = sorin.github.create_pr("org", "repo", "My PR", "body", "my-feature")
sorin.github.comment("org", "repo", pr["pr_number"], "Done!")
```

### LLM inference (one-line swap)

```python
# Before
import anthropic
client = anthropic.Anthropic(api_key="sk-ant-...")

# After — full audit trail, zero other changes
from sorin import SorinLLM
client = SorinLLM(agent_key="<your-sorin-agent-key>")
response = client.messages.create(...)  # identical

# OpenAI
from sorin import SorinOpenAI
client = SorinOpenAI(agent_key="<your-sorin-agent-key>")
response = client.chat.completions.create(...)  # identical
```

## Tool calls grouped by LLM turn

The Activity dashboard groups your agent's tool calls under the LLM turn that triggered them. No setup required — the SDK handles it when you use `SorinLLM` / `SorinOpenAI` and `SorinClient` together.

If a single LLM turn fires multiple parallel tool calls, opt into finer-grained labeling by passing the block id:

```python
response = sorin_llm.messages.create(model=..., messages=..., tools=...)
for block in response.content:
    if block.type == "tool_use":
        sorin.github.push_file(**block.input, tool_use_id=block.id)
```

`tool_use_id` is optional on every `sorin.github.*` method.

## MCP Server (Claude Code & Cursor)

Install the Sorin MCP server with one command:

```bash
# Claude Code
sorin mcp install --key <your-sorin-agent-key>

# Cursor — prints the JSON block to paste into ~/.cursor/mcp.json
sorin mcp install --key <your-sorin-agent-key> --cursor
```

The `sorin` CLI is included with the `sorin-sdk` package (`pip install sorin-sdk`).

## Reference

```
SorinClient(agent_key, base_url="https://sorin-eight.vercel.app")
  .github.list_prs(owner, repo)
  .github.read_file(owner, repo, path, ref="main")
  .github.create_branch(owner, repo, branch, from_branch="main")
  .github.push_file(owner, repo, path, content, message, branch, sha=None)
  .github.create_pr(owner, repo, title, body, head, base="main")
  .github.comment(owner, repo, pr_number, message)

SorinLLM(agent_key, base_url=...)      # drop-in for anthropic.Anthropic
SorinOpenAI(agent_key, base_url=...)   # drop-in for openai.OpenAI
```

## Links

- [trysorin.com](https://trysorin.com)
- [Documentation](https://trysorin.com/docs)
- [PyPI](https://pypi.org/project/sorin-sdk/)
- [GitHub](https://github.com/trysorin/sorin-sdk)
- [Dashboard](https://trysorin.com)
