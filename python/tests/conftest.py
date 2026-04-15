"""Shared fixtures and helpers for the Sorin SDK test suite."""

import os
from typing import Optional

import pytest
import requests

MCP_URL = "https://www.trysorin.com/api/mcp"


@pytest.fixture(scope="session")
def agent_key():
    key = os.getenv("SORIN_AGENT_KEY", "")
    if not key:
        pytest.skip("SORIN_AGENT_KEY not set — skipping integration tests")
    return key


def post_rpc(method: str, params: Optional[dict] = None, key: Optional[str] = None) -> requests.Response:
    """Send a JSON-RPC 2.0 request to the Sorin MCP server."""
    headers = {"Content-Type": "application/json"}
    if key:
        headers["x-agent-key"] = key
    body: dict = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params:
        body["params"] = params
    return requests.post(MCP_URL, json=body, headers=headers, timeout=15)
