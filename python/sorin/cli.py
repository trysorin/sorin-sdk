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
    "--json",
    "print_json",
    is_flag=True,
    default=False,
    help="Print the JSON config block for Cursor, Windsurf, VS Code, or any MCP host that uses mcpServers JSON config.",
)
@click.option(
    "--cursor",
    is_flag=True,
    default=False,
    hidden=True,
    help="Alias for --json (kept for backwards compatibility).",
)
def install(key: str, print_json: bool, cursor: bool) -> None:
    """Install the Sorin MCP server into Claude Code, or print config for other MCP hosts."""
    if print_json or cursor:
        config = {
            "mcpServers": {
                "sorin": {
                    "url": MCP_URL,
                    "headers": {"x-agent-key": key},
                }
            }
        }
        click.echo(
            "Add the following to your MCP settings file and restart your editor:\n"
            "  Cursor:   ~/.cursor/mcp.json\n"
            "  Windsurf: ~/.codeium/windsurf/mcp_config.json\n"
            "  VS Code:  .vscode/mcp.json (workspace) or user settings\n"
        )
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
