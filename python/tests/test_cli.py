"""
Unit tests for sorin/cli.py — the `sorin mcp install` command.

These tests mock subprocess.run so no real `claude` CLI is required.
"""

import json
import subprocess

import pytest
from click.testing import CliRunner

from sorin.cli import cli

MCP_URL = "https://www.trysorin.com/api/mcp"


def _extract_json(output: str) -> dict:
    """Pull the JSON block out of CLI output that may have prose before it."""
    lines = output.strip().split("\n")
    start = next(i for i, line in enumerate(lines) if line.strip().startswith("{"))
    return json.loads("\n".join(lines[start:]))


# ---------------------------------------------------------------------------
# Claude Code install (default — invokes claude mcp add)
# ---------------------------------------------------------------------------

class TestClaudeCodeInstall:
    def test_invokes_claude_mcp_add(self, mocker):
        mock_run = mocker.patch("sorin.cli.subprocess.run")
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="Added", stderr=""
        )
        runner = CliRunner()
        runner.invoke(cli, ["mcp", "install", "--key", "test-key"])
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "claude"
        assert "mcp" in cmd
        assert "add" in cmd

    def test_uses_http_transport(self, mocker):
        mock_run = mocker.patch("sorin.cli.subprocess.run")
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="Added", stderr=""
        )
        runner = CliRunner()
        runner.invoke(cli, ["mcp", "install", "--key", "test-key"])
        cmd = mock_run.call_args[0][0]
        assert "--transport" in cmd
        transport_idx = cmd.index("--transport")
        assert cmd[transport_idx + 1] == "http"

    def test_sets_user_scope(self, mocker):
        mock_run = mocker.patch("sorin.cli.subprocess.run")
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="Added", stderr=""
        )
        runner = CliRunner()
        runner.invoke(cli, ["mcp", "install", "--key", "test-key"])
        cmd = mock_run.call_args[0][0]
        assert "--scope" in cmd
        scope_idx = cmd.index("--scope")
        assert cmd[scope_idx + 1] == "user"

    def test_passes_correct_mcp_url(self, mocker):
        mock_run = mocker.patch("sorin.cli.subprocess.run")
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="Added", stderr=""
        )
        runner = CliRunner()
        runner.invoke(cli, ["mcp", "install", "--key", "test-key"])
        cmd = mock_run.call_args[0][0]
        assert MCP_URL in cmd

    def test_header_comes_after_name_and_url(self, mocker):
        """--header must not precede positional args — it's a variadic flag."""
        mock_run = mocker.patch("sorin.cli.subprocess.run")
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="Added", stderr=""
        )
        runner = CliRunner()
        runner.invoke(cli, ["mcp", "install", "--key", "test-key"])
        cmd = mock_run.call_args[0][0]
        header_idx = cmd.index("--header")
        sorin_idx = cmd.index("sorin")
        url_idx = cmd.index(MCP_URL)
        assert header_idx > sorin_idx
        assert header_idx > url_idx

    def test_header_value_contains_key(self, mocker):
        mock_run = mocker.patch("sorin.cli.subprocess.run")
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="Added", stderr=""
        )
        runner = CliRunner()
        runner.invoke(cli, ["mcp", "install", "--key", "my-secret-key"])
        cmd = mock_run.call_args[0][0]
        header_idx = cmd.index("--header")
        header_value = cmd[header_idx + 1]
        assert "x-agent-key" in header_value
        assert "my-secret-key" in header_value

    def test_prints_success_message_on_success(self, mocker):
        mock_run = mocker.patch("sorin.cli.subprocess.run")
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="Added", stderr=""
        )
        runner = CliRunner()
        result = runner.invoke(cli, ["mcp", "install", "--key", "test-key"])
        assert result.exit_code == 0
        assert "installed" in result.output.lower() or "✓" in result.output

    def test_already_exists_treated_as_success(self, mocker):
        mock_run = mocker.patch("sorin.cli.subprocess.run")
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="already exists"
        )
        runner = CliRunner()
        result = runner.invoke(cli, ["mcp", "install", "--key", "test-key"])
        assert result.exit_code == 0

    def test_subprocess_failure_exits_1(self, mocker):
        mock_run = mocker.patch("sorin.cli.subprocess.run")
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="some unrelated error"
        )
        runner = CliRunner()
        result = runner.invoke(cli, ["mcp", "install", "--key", "test-key"])
        assert result.exit_code == 1

    def test_subprocess_failure_shows_fallback_command(self, mocker):
        mock_run = mocker.patch("sorin.cli.subprocess.run")
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="some unrelated error"
        )
        runner = CliRunner(mix_stderr=False)
        result = runner.invoke(cli, ["mcp", "install", "--key", "test-key"])
        combined = result.output + (result.stderr or "")
        assert "claude mcp add" in combined

    def test_claude_not_found_exits_1(self, mocker):
        mocker.patch("sorin.cli.subprocess.run", side_effect=FileNotFoundError)
        runner = CliRunner()
        result = runner.invoke(cli, ["mcp", "install", "--key", "test-key"])
        assert result.exit_code == 1

    def test_claude_not_found_shows_fallback_command(self, mocker):
        mocker.patch("sorin.cli.subprocess.run", side_effect=FileNotFoundError)
        runner = CliRunner(mix_stderr=False)
        result = runner.invoke(cli, ["mcp", "install", "--key", "test-key"])
        combined = result.output + (result.stderr or "")
        assert "claude mcp add" in combined
        assert MCP_URL in combined


# ---------------------------------------------------------------------------
# --json flag (and --cursor alias)
# ---------------------------------------------------------------------------

class TestJsonFlag:
    def test_prints_valid_json(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["mcp", "install", "--key", "test-key", "--json"])
        parsed = _extract_json(result.output)
        assert isinstance(parsed, dict)

    def test_json_has_mcp_servers_key(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["mcp", "install", "--key", "test-key", "--json"])
        parsed = _extract_json(result.output)
        assert "mcpServers" in parsed

    def test_json_has_sorin_server(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["mcp", "install", "--key", "test-key", "--json"])
        parsed = _extract_json(result.output)
        assert "sorin" in parsed["mcpServers"]

    def test_json_contains_correct_url(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["mcp", "install", "--key", "test-key", "--json"])
        parsed = _extract_json(result.output)
        assert parsed["mcpServers"]["sorin"]["url"] == MCP_URL

    def test_json_contains_x_agent_key_header(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["mcp", "install", "--key", "my-secret-key", "--json"])
        parsed = _extract_json(result.output)
        headers = parsed["mcpServers"]["sorin"]["headers"]
        assert "x-agent-key" in headers
        assert headers["x-agent-key"] == "my-secret-key"

    def test_json_does_not_invoke_subprocess(self, mocker):
        mock_run = mocker.patch("sorin.cli.subprocess.run")
        runner = CliRunner()
        runner.invoke(cli, ["mcp", "install", "--key", "test-key", "--json"])
        mock_run.assert_not_called()

    def test_output_mentions_multiple_editors(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["mcp", "install", "--key", "test-key", "--json"])
        assert "Cursor" in result.output
        assert "Windsurf" in result.output
        assert "VS Code" in result.output

    def test_cursor_flag_is_alias_for_json(self):
        runner = CliRunner()
        json_result = runner.invoke(
            cli, ["mcp", "install", "--key", "test-key", "--json"]
        )
        cursor_result = runner.invoke(
            cli, ["mcp", "install", "--key", "test-key", "--cursor"]
        )
        assert _extract_json(json_result.output) == _extract_json(cursor_result.output)

    def test_cursor_flag_does_not_invoke_subprocess(self, mocker):
        mock_run = mocker.patch("sorin.cli.subprocess.run")
        runner = CliRunner()
        runner.invoke(cli, ["mcp", "install", "--key", "test-key", "--cursor"])
        mock_run.assert_not_called()
