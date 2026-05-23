# sorin

Python SDK for the [Sorin](https://trysorin.com) agent authorization and observability platform.

## Install

```bash
pip install sorin
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

### Agent Actions (GitHub, AWS, etc.)

```python
from sorin import SorinClient

sorin = SorinClient(agent_key="your-agent-key")

# GitHub
file = sorin.github.read_file("your-org", "your-repo", "README.md")
sorin.github.create_branch("your-org", "your-repo", "my-feature")
sorin.github.push_file("your-org", "your-repo", "notes.md", "# Hello", "add notes", "my-feature")
pr = sorin.github.create_pr("your-org", "your-repo", "My PR", "body", "my-feature")

# AWS — S3
buckets = sorin.aws.s3_list_buckets()
objects = sorin.aws.s3_list_objects("my-bucket", prefix="logs/")
obj = sorin.aws.s3_get_object("my-bucket", "path/to/file.json")
sorin.aws.s3_put_object("my-bucket", "output/report.txt", content="done")
sorin.aws.s3_delete_object("my-bucket", "tmp/scratch.txt")

# AWS — EC2
instances = sorin.aws.ec2_describe_instances()
sorin.aws.ec2_start_instance("i-1234567890abcdef0")
sorin.aws.ec2_stop_instance("i-1234567890abcdef0")

# AWS — Lambda
functions = sorin.aws.lambda_list_functions()
result = sorin.aws.lambda_invoke("my-function", payload='{"key": "value"}')
```

Write actions and approval-gated permissions are handled automatically — if a 202 is returned the SDK polls until the request is approved or denied, then retries.

### Tool calls grouped by LLM turn

The Activity dashboard groups your agent's tool calls under the LLM turn that triggered them. No setup required — the SDK handles it when you use `SorinLLM`/`SorinOpenAI` and `SorinClient` together.

If a single LLM turn fires multiple parallel tool calls, opt into finer-grained labeling by passing the block id:

```python
response = sorin_llm.messages.create(model=..., messages=..., tools=...)
for block in response.content:
    if block.type == "tool_use":
        sorin.github.push_file(**block.input, tool_use_id=block.id)
        # or: sorin.aws.s3_put_object(**block.input, tool_use_id=block.id)
```

`tool_use_id` is optional on every `sorin.github.*` and `sorin.aws.*` method.

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
- [PyPI](https://pypi.org/project/sorin/)
- [GitHub](https://github.com/trysorin/sorin-sdk)
- [Dashboard](https://trysorin.com)
