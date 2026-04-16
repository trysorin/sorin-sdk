"""
Verify that parent_request_id auto-threads through Sorin SDK calls via the
contextvar + custom requests.Session machinery.

These tests use `responses` to mock the Sorin proxy and assert on headers.
"""

import json

import pytest
import responses

from sorin import SorinClient
from sorin._context import clear_current_parent, set_current_parent


@pytest.fixture(autouse=True)
def _reset_context():
    """Every test starts with no parent in the contextvar."""
    clear_current_parent()
    yield
    clear_current_parent()


@responses.activate
def test_outbound_call_injects_parent_header_when_context_set():
    """When the contextvar holds a parent, every outbound SorinClient call
    carries the `x-sorin-parent-request-id` header."""
    # Advisory authorize is called first — mock it as allowed.
    responses.add(
        responses.POST,
        "https://trysorin.test/api/runtime/advisory-authorize",
        json={"allowed": True},
        status=200,
    )
    responses.add(
        responses.POST,
        "https://trysorin.test/api/runtime/github/list-pulls",
        json={"pullRequests": []},
        status=200,
    )

    set_current_parent("parent-uuid-from-prior-llm")
    client = SorinClient(agent_key="sk-test", base_url="https://trysorin.test")
    client.github.list_prs(owner="acme", repo="backend")

    tool_call = responses.calls[1].request  # index 0 is advisory-authorize
    assert tool_call.headers.get("X-Sorin-Parent-Request-Id") == "parent-uuid-from-prior-llm"


@responses.activate
def test_outbound_call_omits_parent_header_when_no_context():
    """No parent in contextvar → no header sent. Row lands as orphan root."""
    responses.add(
        responses.POST,
        "https://trysorin.test/api/runtime/advisory-authorize",
        json={"allowed": True},
        status=200,
    )
    responses.add(
        responses.POST,
        "https://trysorin.test/api/runtime/github/list-pulls",
        json={"pullRequests": []},
        status=200,
    )

    client = SorinClient(agent_key="sk-test", base_url="https://trysorin.test")
    client.github.list_prs(owner="acme", repo="backend")

    tool_call = responses.calls[1].request
    assert "X-Sorin-Parent-Request-Id" not in tool_call.headers


@responses.activate
def test_response_header_updates_context():
    """When an upstream response includes `x-sorin-request-id`, the SDK
    captures it so the next call chains to this one. Only LLM routes emit
    this header — simulated here on the mocked response."""
    responses.add(
        responses.POST,
        "https://trysorin.test/api/runtime/advisory-authorize",
        json={"allowed": True},
        status=200,
    )
    responses.add(
        responses.POST,
        "https://trysorin.test/api/runtime/github/list-pulls",
        json={"pullRequests": []},
        status=200,
        headers={"x-sorin-request-id": "new-request-id-from-server"},
    )

    client = SorinClient(agent_key="sk-test", base_url="https://trysorin.test")
    client.github.list_prs(owner="acme", repo="backend")

    from sorin._context import get_current_parent
    assert get_current_parent() == "new-request-id-from-server"
