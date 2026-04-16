"""
The `tool_use_id` kwarg on SorinClient tool methods injects
`x-sorin-tool-use-id` as a per-call header. When omitted, no header is sent.
"""

import pytest
import responses

from sorin import SorinClient
from sorin._context import clear_current_parent


@pytest.fixture(autouse=True)
def _reset_context():
    clear_current_parent()
    yield
    clear_current_parent()


def _mock_authorize_and_tool():
    responses.add(
        responses.POST,
        "https://trysorin.test/api/runtime/advisory-authorize",
        json={"allowed": True},
        status=200,
    )
    responses.add(
        responses.POST,
        "https://trysorin.test/api/runtime/github/push-file",
        json={"path": "x", "sha": "abc", "commit_sha": "def"},
        status=200,
    )


@responses.activate
def test_tool_use_id_kwarg_injects_header():
    _mock_authorize_and_tool()
    client = SorinClient(agent_key="sk-test", base_url="https://trysorin.test")
    client.github.push_file(
        owner="acme", repo="backend", path="src/f.ts",
        content="x", message="c", branch="b",
        tool_use_id="toolu_01ABC",
    )
    push_call = responses.calls[1].request
    assert push_call.headers.get("X-Sorin-Tool-Use-Id") == "toolu_01ABC"


@responses.activate
def test_no_tool_use_id_omits_header():
    _mock_authorize_and_tool()
    client = SorinClient(agent_key="sk-test", base_url="https://trysorin.test")
    client.github.push_file(
        owner="acme", repo="backend", path="src/f.ts",
        content="x", message="c", branch="b",
    )
    push_call = responses.calls[1].request
    assert "X-Sorin-Tool-Use-Id" not in push_call.headers
