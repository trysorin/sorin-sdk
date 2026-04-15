"""
Integration tests for the Sorin MCP server (https://trysorin.com/api/mcp).

These tests hit the real server over HTTP and require SORIN_AGENT_KEY to be set.
They validate the JSON-RPC 2.0 protocol compliance and authentication behavior
without triggering any real upstream actions.
"""

import pytest
import requests

from tests.conftest import MCP_URL, post_rpc


# ---------------------------------------------------------------------------
# initialize — no auth required
# ---------------------------------------------------------------------------

class TestInitialize:
    def test_returns_200(self):
        resp = post_rpc("initialize")
        assert resp.status_code == 200

    def test_returns_correct_protocol_version(self):
        resp = post_rpc("initialize")
        result = resp.json()["result"]
        assert result["protocolVersion"] == "2024-11-05"

    def test_returns_server_info(self):
        resp = post_rpc("initialize")
        info = resp.json()["result"]["serverInfo"]
        assert info["name"] == "sorin"

    def test_returns_tools_capability(self):
        resp = post_rpc("initialize")
        caps = resp.json()["result"]["capabilities"]
        assert "tools" in caps

    def test_sets_mcp_session_id_header(self):
        resp = post_rpc("initialize")
        # Header name may be returned as either casing depending on HTTP layer
        header_names = {k.lower() for k in resp.headers}
        assert "mcp-session-id" in header_names

    def test_does_not_require_auth(self):
        # No key — should still succeed
        resp = post_rpc("initialize")
        data = resp.json()
        assert "error" not in data
        assert "result" in data

    def test_response_is_valid_jsonrpc(self):
        resp = post_rpc("initialize")
        data = resp.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 1


# ---------------------------------------------------------------------------
# tools/list — requires auth
# ---------------------------------------------------------------------------

class TestToolsList:
    def test_valid_key_returns_200(self, agent_key):
        resp = post_rpc("tools/list", key=agent_key)
        assert resp.status_code == 200

    def test_valid_key_returns_tools_array(self, agent_key):
        resp = post_rpc("tools/list", key=agent_key)
        result = resp.json()["result"]
        assert "tools" in result
        assert isinstance(result["tools"], list)

    def test_missing_key_returns_401(self):
        resp = post_rpc("tools/list")
        assert resp.status_code == 401

    def test_missing_key_returns_jsonrpc_error_code(self):
        resp = post_rpc("tools/list")
        data = resp.json()
        assert "error" in data
        assert data["error"]["code"] == -32001

    def test_invalid_key_returns_401(self):
        resp = post_rpc("tools/list", key="sk-sorin-invalid-key-does-not-exist")
        assert resp.status_code == 401

    def test_bearer_token_auth_works(self, agent_key):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {agent_key}",
        }
        body = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
        resp = requests.post(MCP_URL, json=body, headers=headers, timeout=15)
        assert resp.status_code == 200
        assert "tools" in resp.json()["result"]

    def test_x_agent_key_header_auth_works(self, agent_key):
        headers = {
            "Content-Type": "application/json",
            "x-agent-key": agent_key,
        }
        body = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
        resp = requests.post(MCP_URL, json=body, headers=headers, timeout=15)
        assert resp.status_code == 200

    def test_each_tool_has_name_and_description(self, agent_key):
        resp = post_rpc("tools/list", key=agent_key)
        tools = resp.json()["result"]["tools"]
        for tool in tools:
            assert "name" in tool, f"Tool missing 'name': {tool}"
            assert "description" in tool, f"Tool missing 'description': {tool}"


# ---------------------------------------------------------------------------
# ping — requires auth
# ---------------------------------------------------------------------------

class TestPing:
    def test_returns_200(self, agent_key):
        resp = post_rpc("ping", key=agent_key)
        assert resp.status_code == 200

    def test_returns_empty_result(self, agent_key):
        resp = post_rpc("ping", key=agent_key)
        assert resp.json()["result"] == {}

    def test_missing_key_returns_401(self):
        resp = post_rpc("ping")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# tools/call — error cases only (no real upstream actions triggered)
# ---------------------------------------------------------------------------

class TestToolsCallErrors:
    def test_missing_tool_name_returns_invalid_params(self, agent_key):
        resp = post_rpc("tools/call", params={"arguments": {}}, key=agent_key)
        data = resp.json()
        assert "error" in data
        assert data["error"]["code"] == -32602

    def test_unknown_tool_returns_invalid_params(self, agent_key):
        resp = post_rpc(
            "tools/call",
            params={"name": "nonexistent_tool_xyz", "arguments": {}},
            key=agent_key,
        )
        data = resp.json()
        assert "error" in data
        assert data["error"]["code"] == -32602

    def test_missing_key_returns_401(self):
        resp = post_rpc(
            "tools/call",
            params={"name": "github_list_pulls", "arguments": {}},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Unknown method
# ---------------------------------------------------------------------------

class TestUnknownMethod:
    def test_unknown_method_returns_method_not_found(self, agent_key):
        resp = post_rpc("unknown/method", key=agent_key)
        data = resp.json()
        assert "error" in data
        assert data["error"]["code"] == -32601

    def test_invalid_jsonrpc_version_returns_error(self):
        body = {"jsonrpc": "1.0", "id": 1, "method": "ping"}
        resp = requests.post(
            MCP_URL,
            json=body,
            headers={"Content-Type": "application/json"},
            timeout=15,
        )
        data = resp.json()
        assert "error" in data
