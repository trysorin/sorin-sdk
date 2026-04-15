import json
import subprocess
import sys

import click

MCP_URL = "https://trysorin.com/api/mcp"


@click.group()
def cli():
    """Sorin SDK command-line tools."""


@cli.group()
def mcp():
    """MCP server management commands."""


@mcp.command()
@click.option("--key", required=True, help="Your Sorin agent key.")
@click.option(
    "--cursor",
    is_flag=True,
    default=False,
    help="Print the JSON config block for Cursor's MCP settings instead of running the CLI command.",
)
def install(key: str, cursor: bool) -> None:
    """Install the Sorin MCP server into Claude Code (or print Cursor config)."""
    if cursor:
        config = {
            "mcpServers": {
                "sorin": {
                    "url": MCP_URL,
                    "headers": {"x-agent-key": key},
                }
            }
        }
        click.echo("Paste the following into your Cursor MCP settings (~/.cursor/mcp.json):\n")
        click.echo(json.dumps(config, indent=2))
        return

    cmd = [
        "claude", "mcp", "add",
        "--transport", "http",
        "--scope", "user",
        "sorin",
        MCP_URL,
        "--header", f"x-agent-key: {key}",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        combined = result.stdout + result.stderr

        if result.returncode == 0 or "already exists" in combined:
            click.echo("✓ Sorin MCP server installed. Restart Claude Code to connect.")
        else:
            click.echo(
                f"Error: `claude mcp add` failed (exit code {result.returncode}).\n\n"
                "Run the following command manually instead:\n\n"
                f"  claude mcp add --transport http --scope user sorin {MCP_URL} --header \"x-agent-key: {key}\"",
                err=True,
            )
            sys.exit(1)
    except FileNotFoundError:
        click.echo(
            "Error: the `claude` CLI was not found. Make sure Claude Code is installed and on your PATH.\n\n"
            "Run the following command manually instead:\n\n"
            f"  claude mcp add --transport http --scope user sorin {MCP_URL} --header \"x-agent-key: {key}\"",
            err=True,
        )
        sys.exit(1)


def main() -> None:
    cli()
